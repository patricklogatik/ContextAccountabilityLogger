# ContextAccountabilityLogger

ContextAccountabilityLogger is a personal productivity companion that captures
keystrokes, clipboard updates, active window changes, and periodic screenshots
while displaying a lightweight focus overlay. The collected data is stored in a
daily folder structure so you can review how you spent your time and keep an
audit trail for future reflection.

⚠️ **Privacy notice:** This tool records extremely sensitive information
(screenshots, keystrokes, and clipboard contents). Only run it on machines you
own and where all users have provided informed consent.

## Features

- 🍏 Apple-inspired floating overlay to set short-term goals and timers.
- ⌨️ Keystroke logging with periodic flushes to disk and JSON activity log.
- 📋 Clipboard monitoring with timestamps for each captured snippet.
- 🪟 Active window tracking with per-application usage summaries (Windows only).
- 🖼️ Automatic screenshots every 10 seconds across single or multiple monitors.
- 📊 Session summaries that include usage statistics and top applications.

## Requirements

- Python 3.9 or newer.
- The Python packages listed in [`requirements.txt`](requirements.txt).
- Platform-specific dependencies:
  - **Windows:** No additional setup is required. Active window tracking relies
    on the Win32 APIs via `pywin32`.
  - **macOS / Linux:** Active window tracking is disabled because the Win32
    APIs are unavailable. Clipboard monitoring on Linux may require the `xclip`
    or `xsel` utility, and screenshots require an X11 or Wayland backend that
    Pillow can access.

## Installation

1. Clone the repository and enter the project folder:

   ```bash
   git clone https://github.com/<your-account>/ContextAccountabilityLogger.git
   cd ContextAccountabilityLogger
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the tracker directly with Python:

```bash
python recorder.py
```

On first launch you will be prompted for:

- A directory where logs should be stored.
- How frequently keystrokes are flushed to disk (15/30/60 seconds).

These settings are saved in `tracker_config.json` so subsequent runs start
immediately. A Windows shortcut is available via `start_recorder.bat`.

While the program is running you can:

- Press `Ctrl+Q` or click the gear icon on the overlay to set a new focus goal.
- Review real-time status updates in the console.
- Stop the tracker with `Ctrl+C` in the terminal.

All logs for the current day are written to `<log_folder>/<YYYY-MM-DD>/` and
include:

- `activity_log.json` – unified structured event log.
- `keystrokes.txt` – keystrokes grouped by flush interval.
- `clipboard.txt` – clipboard captures with timestamps.
- `windows.txt` – active window transitions (Windows only).
- `events.txt` – human-readable event stream.
- `app_usage_summary.json` – minutes spent per application.
- `session_summary.json` – overall statistics for the session.
- `screenshots/` – timestamped PNG captures every 10 seconds.

## Troubleshooting

- **Permission errors:** Run the terminal as an administrator (Windows) or
  ensure you have sufficient permissions to listen to global input events.
- **Clipboard errors on Linux:** Install `xclip` or `xsel` and ensure an X11 or
  Wayland session is available.
- **Screenshots failing:** Verify that Pillow can access your display server. On
  headless systems you may need to use a virtual display such as Xvfb.
- **Window tracking disabled:** This is expected on non-Windows platforms. The
  rest of the logging functionality will continue to run normally.

## License

This project is licensed under the terms of the [MIT License](LICENSE).
