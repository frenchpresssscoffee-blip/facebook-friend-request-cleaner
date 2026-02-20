# Facebook Request Cleaner

Bulk-clear Facebook friend requests using browser automation with Playwright.

## Features

- Clear incoming friend requests (`Delete`/`Remove`)
- Clear outgoing friend requests (`Cancel request`)
- Persistent browser profile so login is reused between runs
- Choose how many people to process each run with `--max-actions`
- `--dry-run` mode to preview matches without clicking
- Confirmation prompt before destructive runs (or bypass with `--yes`)
- Custom label matching and URL overrides for localization/UI differences

## Requirements

- Python 3.9+
- Chromium browser runtime for Playwright

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

## Usage

```powershell
python facebook_clear_requests.py --browser auto --mode both --max-actions 300
python facebook_clear_requests.py --mode incoming
python facebook_clear_requests.py --mode outgoing
python facebook_clear_requests.py --mode both --max-actions 300
python facebook_clear_requests.py --mode both --dry-run
python facebook_clear_requests.py --incoming-labels "delete,remove" --outgoing-labels "cancel request,cancel"
```

### CLI options

- `--browser` : Browser to use: `auto`, `chrome`, `edge`, `chromium`, or `firefox`. `auto` tries installed Chrome/Edge first.
- `--mode` : Which requests to process: `incoming`, `outgoing`, or `both` (default).
- `--max-actions` : Maximum number of people to process in one run. Example: `--max-actions 100`.
- `--profile-dir` : Folder where browser login data is saved so you stay signed in.
- `--pause` : Seconds to wait between clicks.
- `--headless` : Run browser in background (no visible window).
- `--max-stuck-loops` : Stop after this many no-progress scroll loops.
- `--incoming-labels` : Button words for incoming requests (comma-separated).
- `--outgoing-labels` : Button words for outgoing requests (comma-separated).
- `--incoming-url` / `--outgoing-url` : Custom request page URLs.
- `--dry-run` : Preview matches only (no clicks).
- `--yes` : Skip confirmation prompt and start immediately.

## Notes

- First run may require manual login and 2FA in the opened browser window.
- `--browser auto` tries installed Chrome first, then Edge, then Playwright Chromium.
- Facebook UI changes can break selectors or button labels; update patterns in the script as needed.
- Use responsibly and in compliance with Facebook Terms.

## Project Structure

```text
facebook-request-cleaner/
  facebook_clear_requests.py
  requirements.txt
  .gitignore
  README.md
```

