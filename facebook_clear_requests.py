#!/usr/bin/env python3
"""
Bulk-clear Facebook friend requests using browser automation.

Usage:
  python facebook_clear_requests.py --mode incoming
  python facebook_clear_requests.py --mode outgoing
  python facebook_clear_requests.py --mode both --max-actions 300
  python facebook_clear_requests.py --mode both --dry-run

Requirements:
  pip install playwright
  playwright install chromium
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import Error, TimeoutError, sync_playwright


INCOMING_URL = "https://www.facebook.com/friends/requests/"
OUTGOING_URL = "https://www.facebook.com/friends/center/requests/outgoing/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete Facebook friend requests in bulk."
    )
    parser.add_argument(
        "--mode",
        choices=["incoming", "outgoing", "both"],
        default="both",
        help="Which request list to clear.",
    )
    parser.add_argument(
        "--max-actions",
        type=int,
        default=500,
        help="Safety cap for total clicks.",
    )
    parser.add_argument(
        "--profile-dir",
        default="facebook_profile",
        help="Browser profile dir (keeps login session).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without visible browser window.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.7,
        help="Delay between actions in seconds.",
    )
    parser.add_argument(
        "--max-stuck-loops",
        type=int,
        default=8,
        help="How many no-progress scroll loops before stopping.",
    )
    parser.add_argument(
        "--incoming-labels",
        default="delete,delete request,remove",
        help="Comma-separated labels to match for incoming requests.",
    )
    parser.add_argument(
        "--outgoing-labels",
        default="cancel request,cancel",
        help="Comma-separated labels to match for outgoing requests.",
    )
    parser.add_argument(
        "--incoming-url",
        default=INCOMING_URL,
        help="Override URL for incoming request page.",
    )
    parser.add_argument(
        "--outgoing-url",
        default=OUTGOING_URL,
        help="Override URL for outgoing request page.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect and print matching buttons without clicking.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip destructive action confirmation prompt.",
    )
    return parser.parse_args()


def ensure_logged_in(page) -> None:
    page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    time.sleep(1.0)

    if page.locator('input[name="email"]').count() > 0:
        print("Login is required.")
        print("1) Sign in to Facebook in the opened browser.")
        print("2) Complete any 2FA/checkpoint prompts.")
        input("Press ENTER here once you are fully logged in: ")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")

    if page.locator('input[name="email"]').count() > 0:
        raise RuntimeError("Still on login page. Could not continue.")


def text_matches(text: str, patterns: list[re.Pattern[str]]) -> bool:
    clean = re.sub(r"\s+", " ", text).strip()
    return any(p.search(clean) for p in patterns)


def compile_patterns(raw_labels: str) -> list[re.Pattern[str]]:
    labels = [item.strip() for item in raw_labels.split(",") if item.strip()]
    if not labels:
        raise ValueError("At least one non-empty label is required.")
    return [re.compile(re.escape(label), re.IGNORECASE) for label in labels]


def click_matching_buttons(
    page,
    label_patterns: list[re.Pattern[str]],
    max_actions: int,
    pause: float,
    dry_run: bool,
    max_stuck_loops: int,
) -> dict[str, int]:
    actions = 0
    stuck_loops = 0
    previous_height = 0
    scanned_buttons = 0
    matched_buttons = 0
    click_errors = 0
    while actions < max_actions and stuck_loops < max_stuck_loops:
        clicked_this_pass = 0
        buttons = page.locator("button, div[role='button']")

        try:
            total = buttons.count()
        except Error:
            total = 0

        for i in range(total):
            if actions >= max_actions:
                break

            btn = buttons.nth(i)

            try:
                if not btn.is_visible():
                    continue
                text = btn.inner_text(timeout=600)
            except (Error, TimeoutError):
                continue
            scanned_buttons += 1

            if not text_matches(text, label_patterns):
                continue
            matched_buttons += 1

            if dry_run:
                print(f"[DRY RUN] Match: {text.strip()!r}")
                continue

            try:
                btn.scroll_into_view_if_needed(timeout=800)
                btn.click(timeout=1200)
                actions += 1
                clicked_this_pass += 1
                print(f"Clicked {actions}: {text.strip()!r}")
                time.sleep(pause)
            except (Error, TimeoutError):
                click_errors += 1
                continue

        if clicked_this_pass == 0:
            try:
                current_height = page.evaluate("document.body.scrollHeight")
            except Error:
                current_height = previous_height

            page.mouse.wheel(0, 1800)
            time.sleep(1.0)

            if current_height <= previous_height:
                stuck_loops += 1
            else:
                stuck_loops = 0
                previous_height = current_height
        else:
            stuck_loops = 0

    return {
        "clicked": actions,
        "scanned": scanned_buttons,
        "matched": matched_buttons,
        "click_errors": click_errors,
    }


def clear_requests(
    page,
    section_name: str,
    url: str,
    patterns: list[re.Pattern[str]],
    limit: int,
    pause: float,
    dry_run: bool,
    max_stuck_loops: int,
) -> dict[str, int]:
    print(f"\nProcessing {section_name} requests...")
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(1.0)

    result = click_matching_buttons(
        page=page,
        label_patterns=patterns,
        max_actions=limit,
        pause=pause,
        dry_run=dry_run,
        max_stuck_loops=max_stuck_loops,
    )
    return result


def main() -> int:
    args = parse_args()
    profile_dir = str(Path(args.profile_dir).resolve())
    try:
        incoming_patterns = compile_patterns(args.incoming_labels)
        outgoing_patterns = compile_patterns(args.outgoing_labels)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            profile_dir,
            headless=args.headless,
            viewport={"width": 1366, "height": 900},
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            ensure_logged_in(page)
        except RuntimeError as exc:
            print(f"Error: {exc}")
            context.close()
            return 1

        if not args.dry_run and not args.yes:
            print("\nThis will click buttons that remove/cancel friend requests.")
            confirm = input("Type YES to continue: ").strip()
            if confirm != "YES":
                print("Aborted by user.")
                context.close()
                return 0

        total_done = 0
        remaining = args.max_actions
        incoming_result = {"clicked": 0, "scanned": 0, "matched": 0, "click_errors": 0}
        outgoing_result = {"clicked": 0, "scanned": 0, "matched": 0, "click_errors": 0}

        if args.mode in ("incoming", "both") and remaining > 0:
            incoming_result = clear_requests(
                page=page,
                section_name="incoming",
                url=args.incoming_url,
                patterns=incoming_patterns,
                limit=remaining,
                pause=args.pause,
                dry_run=args.dry_run,
                max_stuck_loops=args.max_stuck_loops,
            )
            total_done += incoming_result["clicked"]
            remaining -= incoming_result["clicked"]

        if args.mode in ("outgoing", "both") and remaining > 0:
            outgoing_result = clear_requests(
                page=page,
                section_name="outgoing",
                url=args.outgoing_url,
                patterns=outgoing_patterns,
                limit=remaining,
                pause=args.pause,
                dry_run=args.dry_run,
                max_stuck_loops=args.max_stuck_loops,
            )
            total_done += outgoing_result["clicked"]
            remaining -= outgoing_result["clicked"]

        print("\nSummary")
        print(
            "Incoming: "
            f"clicked={incoming_result['clicked']}, "
            f"matched={incoming_result['matched']}, "
            f"scanned={incoming_result['scanned']}, "
            f"errors={incoming_result['click_errors']}"
        )
        print(
            "Outgoing: "
            f"clicked={outgoing_result['clicked']}, "
            f"matched={outgoing_result['matched']}, "
            f"scanned={outgoing_result['scanned']}, "
            f"errors={outgoing_result['click_errors']}"
        )
        if args.dry_run:
            print("Dry run mode: no clicks were made.")
        print(f"Total actions: {total_done}")
        print("Browser profile saved; you can rerun without logging in again.")

        context.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
