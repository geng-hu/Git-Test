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

try:
    from waveshare_epd import epd2in8
except Exception:
    print("Error: could not import waveshare_epd. Install 'waveshare-epd' package.")
    raise

from PIL import Image, ImageDraw, ImageFont


def load_font(path=None, size=36):
    try:
        if path:
            return ImageFont.truetype(path, size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def render_and_display(epd, time_str, date_str, font_time, font_date):
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

    epd.display(epd.getbuffer(image))


def main():
    parser = argparse.ArgumentParser(description="Display date/time on Waveshare 2.8 e-ink")
    parser.add_argument("--interval", type=int, default=60, help="Update interval in seconds (default: 60)")
    parser.add_argument("--font", type=str, default=None, help="TTF font path to use")
    parser.add_argument("--font-size", type=int, default=48, help="Font size for time")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear display on exit")
    parser.add_argument("--show-seconds", action="store_true", help="Show seconds in time display")
    args = parser.parse_args()

    try:
        epd = epd2in8.EPD()
        epd.init()
        epd.Clear(0xFF)
    except Exception as e:
        print("Failed to initialize e-Paper display:", e)
        sys.exit(1)

    font_time = load_font(args.font, args.font_size)
    font_date = load_font(args.font, max(14, args.font_size // 3))

    try:
        while True:
            now = datetime.now()
            if args.show_seconds:
                time_str = now.strftime('%H:%M:%S')
            else:
                time_str = now.strftime('%H:%M')
            date_str = now.strftime('%Y-%m-%d')

            render_and_display(epd, time_str, date_str, font_time, font_date)

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
