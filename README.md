# Facebook Request Cleaner

Bulk-clear Facebook friend requests using browser automation with Playwright.

## Features

- Clear incoming friend requests (`Delete`/`Remove`)
- Clear outgoing friend requests (`Cancel request`)
- Persistent browser profile so login is reused between runs
- Safety cap for max clicks per run
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
python facebook_clear_requests.py --mode incoming
python facebook_clear_requests.py --mode outgoing
python facebook_clear_requests.py --mode both --max-actions 300
python facebook_clear_requests.py --mode both --dry-run
python facebook_clear_requests.py --incoming-labels "delete,remove" --outgoing-labels "cancel request,cancel"
```

### CLI options

- `--mode` : `incoming`, `outgoing`, `both` (default)
- `--max-actions` : max number of clicks in one run (default `500`)
- `--profile-dir` : directory for persistent login session (default `facebook_profile`)
- `--pause` : delay between clicks in seconds (default `0.7`)
- `--headless` : run browser without UI
- `--max-stuck-loops` : stop after N scroll loops with no progress (default `8`)
- `--incoming-labels` : comma-separated labels to match for incoming requests
- `--outgoing-labels` : comma-separated labels to match for outgoing requests
- `--incoming-url` / `--outgoing-url` : override request page URLs
- `--dry-run` : print matches without clicking
- `--yes` : skip confirmation prompt

## Notes

- First run may require manual login and 2FA in the opened browser window.
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

