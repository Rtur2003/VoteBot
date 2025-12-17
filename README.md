![VOTRYX Banner](docs/screenshots/votryx-banner-dark.png)

# VOTRYX

Automated Voting Intelligence for DistroKid

<p align="center">
  <img src="docs/screenshots/votryx-logo-transparent.png" alt="VOTRYX Logo" width="260" />
</p>
<p align="center"><em>SVG version available for scalable embeds.</em></p>

## Overview
VOTRYX is a Tkinter-based control surface for automated voting workflows on DistroKid Spotlight, combining Selenium-driven browser automation with guarded start/stop controls, structured logging, and recoverable preflight checks. The application focuses on predictable behavior, configurable safety limits, and visibility into every action.

## Migration Note
Previously known as VoteBot; existing configs and workflows remain compatible under the new VOTRYX branding.

## Screenshots
![VOTRYX Control Interface](docs/screenshots/votebot5-ui.png)  
*VOTRYX Control Interface*

## Features
- Driver/Chrome preflight with version compatibility checks.
- Guarded start/stop flow, status badges, file + UI logging.
- Batch and parallel voting with adjustable batch size and window count.
- Random user-agent pool and optional image blocking toggles.
- Fallback vote selectors (CSS/XPath) with failure screenshots.
- Backoff after consecutive errors, timeouts, and profile/session cleanup.

## Requirements
- Python 3.9+
- Google Chrome (installed)
- Matching ChromeDriver (`chromedriver.exe`) or Selenium Manager
- `pip install -r requirements.txt` (selenium)

## Setup
```bash
cd "C:\Users\MONSTER\Desktop\VOTRYX"
pip install -r requirements.txt
```

### ChromeDriver
- Check Chrome version: `chrome --version`
- Download ChromeDriver matching the major version: https://googlechromelabs.github.io/chrome-for-testing/
- Place `chromedriver.exe` in the project root: `C:\Users\MONSTER\Desktop\VOTRYX\chromedriver.exe`
- Alternative: set `use_selenium_manager = true` to let Selenium Manager download/update (requires internet).

## Configuration
`config.json` (project root) or `Code_EXE/Votryx/config.json`:
```json
{
  "paths": {
    "chrome": "C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe",
    "driver": "chromedriver.exe",
    "logs": "logs",
    "config": "config.json"
  },
  "target_url": "https://distrokid.com/spotlight/hasanarthuraltunta/vote/",
  "pause_between_votes": 3,
  "batch_size": 1,
  "max_errors": 3,
  "parallel_workers": 2,
  "headless": true,
  "timeout_seconds": 15,
  "use_selenium_manager": false,
  "use_random_user_agent": true,
  "block_images": true,
  "user_agents": [],
  "vote_selectors": [
    "a[data-action='vote']",
    "button[data-action='vote']",
    "xpath://a[contains(translate(., 'VOTE', 'vote'), 'vote')]"
  ],
  "backoff_seconds": 5,
  "backoff_cap_seconds": 60
}
```
- `driver` and `logs` resolve relative to the project root if not absolute.
- `parallel_workers`: concurrent browser windows (1-10).
- `headless`: show/hide the browser.
- `use_selenium_manager`: auto-manage driver if enabled.
- `use_random_user_agent`: pick from the UA pool; otherwise use Chrome default.
- `block_images`: speed up by blocking images.
- `vote_selectors`: additional CSS/XPath options; first match wins.
- `backoff_seconds` / `backoff_cap_seconds`: wait after consecutive errors, with a capped backoff.

## Running
```bash
python Code_EXE/Votryx/VotryxApp.py
```
1) Preflight: paths and versions validated; issues reported.  
2) Start: automation runs, counters and logs update live.  
3) Stop: clean shutdown.  
4) Log shortcut opens `logs/votryx.log`.

## Git
```bash
git remote add origin https://github.com/Rtur2003/VOTRYX.git
git branch -M main
git pull --rebase origin main   # fetch history
git push -u origin main
```

## Brand Assets
- Primary banner: `docs/screenshots/votryx-banner-dark.png`
- Secondary banner (optional): `docs/screenshots/votryx-banner-2-dark.png`
- Logos: `docs/screenshots/votryx-logo-transparent.png`, `docs/screenshots/votryx-logo-transparent.svg`, `docs/screenshots/votryx-logo-3-dark.png`, `docs/screenshots/votryx-logo-4.png.png`
- ASCII logo: `docs/screenshots/ASCII-LOGO.png`
