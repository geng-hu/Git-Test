Raspberry Pi Zero 2W — Waveshare 2.8" e-Paper Time Display

Overview
- Small Python script to show current date and time on a Waveshare 2.8 inch e-ink display.
- Designed for Raspberry Pi Zero 2 W with SPI enabled and the Waveshare e-Paper module wired per the vendor docs.

Files
- `display_time.py`: main script to run on the Pi and update the display.
- `requirements.txt`: Python dependencies.

Quick setup
1. Enable SPI (use `raspi-config` -> Interface Options -> SPI) and reboot.
2. Install dependencies:

```bash
sudo apt update
sudo apt install -y python3-pip python3-pil python3-dev
pip3 install -r requirements.txt
```

3. Wiring and driver
- Connect the Waveshare 2.8" e-Paper to the Pi SPI pins and power. Follow Waveshare hardware docs for your exact HAT/board variant.
- The script uses the `waveshare-epd` Python package (common community driver). If you installed vendor drivers from Waveshare GitHub, confirm that `epd2in8` is importable.
- The script uses the `waveshare-epd` Python package (common community driver). This version of the script targets the `epd2in13_v4` driver; if you installed vendor drivers from Waveshare GitHub, confirm that `epd2in13_v4` is importable.

Run

```bash
sudo python3 display_time.py --interval 60
```

Options
- `--interval`: update interval in seconds (default 60). For e-ink displays, avoid very small intervals to reduce wear.
- `--font`: path to a TTF font to use (defaults to DejaVu Sans if available).
- `--font-size`: font size for the time text (default 48).
- `--show-seconds`: include seconds in the time display.
- `--no-clear`: do not clear the display on program exit.

- `--model`: removed — this script targets `epd2in13_v4` specifically.

New / notable options
- `--partial-refresh`: attempt to use the e-ink driver's partial-refresh API when available. Falls back to a full refresh if the driver does not expose a compatible method. Use this to reduce flicker and speed up updates when your module supports partial updates.

Behavior changes
- IP addresses: the script now detects and displays local IP addresses on the screen by default (shown beneath the date). If you prefer to hide IPs, run the script inside a wrapper or request a `--no-ips` option.

Systemd service example
- Create `/etc/systemd/system/eink-time.service` with:

```ini
[Unit]
Description=E-Ink Time Display
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pi/display_time.py --interval 60
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Then enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now eink-time.service
```

Notes and caveats
- This script performs full-screen updates. Some Waveshare modules support partial refresh; adapt to your board's API if available (e.g., `displayPartial`).
- Test fonts and sizes locally before deploying. If `DejaVuSans` is missing, pass `--font` to use a bundled TTF.

Partial refresh notes
- Partial refresh support depends on your specific Waveshare driver variant. The script tries common partial methods (e.g. `displayPartial`, `display_partial`) and will print a short message and fall back to full refresh if none are available. If you installed a vendor driver from Waveshare, check its API for a partial-update function and report the method name if you want it added to the detection list.

Troubleshooting
- Import errors: ensure `waveshare-epd` is installed and matches your board model.
- No display: verify SPI is enabled and wiring is correct, and check vendor docs for power requirements.

Feedback
- Tell me preferred layout (24h vs 12h), whether you want weather or additional info, and whether your e-ink supports partial updates so I can adapt the code.
