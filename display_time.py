#!/usr/bin/env python3
"""
Simple script for Waveshare 2.8" e-Paper to show date and time on Raspberry Pi Zero 2 W.

Usage: sudo python3 display_time.py

Notes:
- Requires SPI enabled and wiring connected per Waveshare instructions.
- Uses `waveshare-epd` and `Pillow`.
"""
import time
import sys
import argparse
from datetime import datetime
import subprocess
import shlex




from PIL import Image, ImageDraw, ImageFont


def load_font(path=None, size=36):
    try:
        if path:
            return ImageFont.truetype(path, size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def render_and_display(epd, time_str, date_str, font_time, font_date, partial=False):
    width, height = epd.width, epd.height
    image = Image.new('1', (width, height), 255)  # 1: 1-bit color
    draw = ImageDraw.Draw(image)

    # layout: time large, date smaller under it
    w_time, h_time = draw.textsize(time_str, font=font_time)
    w_date, h_date = draw.textsize(date_str, font=font_date)

    x_time = (width - w_time) // 2
    y_time = max(2, (height // 2 - h_time))

    x_date = (width - w_date) // 2
    y_date = y_time + h_time + 4

    draw.text((x_time, y_time), time_str, fill=0, font=font_time)
    draw.text((x_date, y_date), date_str, fill=0, font=font_date)

    display_image(epd, image, partial_requested=partial)


def get_ip_addresses():
    """Return a list of IP address strings. Try `ip` command first, then fallback to primary socket trick."""
    addrs = []
    try:
        # Prefer `ip -o addr` which lists interfaces and addresses in a parseable form
        out = subprocess.check_output(shlex.split("ip -o addr show"), stderr=subprocess.DEVNULL)
        for line in out.decode().splitlines():
            # example: '2: eth0    inet 192.168.1.10/24 brd ...'
            parts = line.split()
            if len(parts) >= 4 and parts[2] in ("inet", "inet6"):
                iface = parts[1]
                addr = parts[3].split('/')[0]
                if addr and not addr.startswith('127.') and addr != '::1':
                    addrs.append(f"{iface}: {addr}")
    except Exception:
        # Fallback: determine primary outbound IPv4 address
        try:
            s = __import__('socket').socket(__import__('socket').AF_INET, __import__('socket').SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip:
                addrs.append(f"primary: {ip}")
        except Exception:
            pass

    # Deduplicate and limit to a few lines for display
    seen = []
    for a in addrs:
        if a not in seen:
            seen.append(a)
    return seen[:3]


def display_image(epd, image, partial_requested=False):
    """Display an image on the epd device.

    If `partial_requested` is True, attempt to call any available partial-refresh
    method on the driver (common names tried). Falls back to full `display()`.
    """
    buf = None
    try:
        buf = epd.getbuffer(image)
    except Exception:
        try:
            # Some drivers accept the raw image; try passing image directly
            buf = image
        except Exception:
            buf = None

    if buf is None:
        try:
            epd.display(epd.getbuffer(image))
        except Exception:
            pass
        return

    # Try common partial refresh method names
    partial_methods = ("displayPartial", "DisplayPartial", "display_partial", "display_partial_buffer", "partial_update")
    if partial_requested:
        for name in partial_methods:
            if hasattr(epd, name):
                try:
                    getattr(epd, name)(buf)
                    return
                except Exception:
                    # If calling fails, try the next one
                    continue
        # If we reach here, no partial method worked — fall back to full display
        try:
            print("Partial refresh requested but not supported by driver; using full refresh.")
        except Exception:
            pass

    # Default: full display
    try:
        if hasattr(epd, 'display'):
            epd.display(buf)
        else:
            # fallback: try any callable attribute that looks like display
            for attr in dir(epd):
                if 'display' in attr.lower():
                    fn = getattr(epd, attr)
                    if callable(fn):
                        try:
                            fn(buf)
                            return
                        except Exception:
                            continue
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Display date/time on Waveshare 2.8 e-ink")
    parser.add_argument("--interval", type=int, default=60, help="Update interval in seconds (default: 60)")
    parser.add_argument("--font", type=str, default=None, help="TTF font path to use")
    parser.add_argument("--font-size", type=int, default=48, help="Font size for time")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear display on exit")
    parser.add_argument("--show-seconds", action="store_true", help="Show seconds in time display")
    parser.add_argument("--partial-refresh", dest="partial_refresh", action="store_true",
                        help="Use e-ink partial refresh if supported (falls back to full refresh)")
    # --model removed; this script targets epd2in13_v4 specifically
    args = parser.parse_args()

    try:
        from waveshare_epd import epd2in13_v4
        epd = epd2in13_v4.EPD()
        epd.init()
        epd.Clear(0xFF)
    except Exception as e:
        print("Failed to initialize e-Paper display:", e)
        sys.exit(1)

    font_time = load_font(args.font, args.font_size)
    font_date = load_font(args.font, max(14, args.font_size // 3))
    font_ip = load_font(args.font, max(12, args.font_size // 4))

    try:
        while True:
            now = datetime.now()
            if args.show_seconds:
                time_str = now.strftime('%H:%M:%S')
            else:
                time_str = now.strftime('%H:%M')
            date_str = now.strftime('%Y-%m-%d')

            ips = get_ip_addresses()
            render_and_display(epd, time_str, date_str, font_time, font_date, partial=args.partial_refresh)

            # Draw IPs directly after rendering the main image to keep layout simple
            if ips:
                try:
                    # Recreate image and draw IP lines under the date
                    width, height = epd.width, epd.height
                    image = Image.new('1', (width, height), 255)
                    draw = ImageDraw.Draw(image)

                    w_time, h_time = draw.textsize(time_str, font=font_time)
                    x_time = (width - w_time) // 2
                    y_time = max(2, (height // 2 - h_time))

                    w_date, h_date = draw.textsize(date_str, font=font_date)
                    x_date = (width - w_date) // 2
                    y_date = y_time + h_time + 4

                    draw.text((x_time, y_time), time_str, fill=0, font=font_time)
                    draw.text((x_date, y_date), date_str, fill=0, font=font_date)

                    # IP lines
                    y = y_date + h_date + 6
                    for ip_line in ips:
                        w_ip, h_ip = draw.textsize(ip_line, font=font_ip)
                        x_ip = (width - w_ip) // 2
                        if y + h_ip > height - 2:
                            break
                        draw.text((x_ip, y), ip_line, fill=0, font=font_ip)
                        y += h_ip + 2

                    display_image(epd, image, partial_requested=args.partial_refresh)
                except Exception:
                    # If anything fails while drawing IPs, ignore and continue
                    pass

            # For e-ink, avoid very frequent full updates. Sleep until next interval.
            for _ in range(max(1, args.interval)):
                time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        if not args.no_clear:
            try:
                epd.Clear(0xFF)
            except Exception:
                pass
        try:
            epd.sleep()
        except Exception:
            pass


if __name__ == '__main__':
    main()
