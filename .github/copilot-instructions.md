<!-- .github/copilot-instructions.md - guidance for AI coding agents -->
# Repo guidance for AI coding agents

This repo is a tiny, single-purpose Python project that runs on a Raspberry Pi Zero 2 W and drives a Waveshare 2.8" e-Paper display. Its core is a single script: `display_time.py`.

Key facts (quick):
- Purpose: show date/time on a Waveshare e-ink module using `waveshare_epd.epd2in8`.
- Platform: Raspberry Pi (requires SPI enabled) — do not attempt to run hardware-specific integration on non-Pi containers unless explicitly mocked.
- Entrypoint: `display_time.py` (args: `--interval`, `--font`, `--font-size`, `--show-seconds`, `--no-clear`).
- Dependencies: listed in `requirements.txt` (Pillow, waveshare-epd). See `README.md` for install/run steps and a systemd example.

What an AI agent should prioritize
- Preserve the single-file design: the project intentionally keeps logic in `display_time.py`. Keep changes minimal and focused unless the user asks for refactoring.
- Hardware safety: any code that touches SPI/display initialization (`epd2in8.EPD().init()`, `Clear`, `sleep`) must be gated or mocked in tests. Add explicit checks/flags for dry-run/mock mode if introducing CI tests.
- Avoid frequent full refreshes: the script intentionally throttles updates (`--interval`) and warns about e-ink wear. If optimizing updates, prefer optional partial-refresh code paths and expose them behind feature flags.

Patterns and examples from the codebase
- Font loading fallback: `load_font(path, size)` uses a TTF if provided, else tries DejaVu, else falls back to `ImageFont.load_default()` — preserve this graceful fallback when changing display rendering.
- Display lifecycle: the code calls `epd.init()`, `epd.Clear(0xFF)`, and `epd.sleep()` in `finally` blocks. Respect this pattern when adding features so the display is always left in a stable state.
- CLI-first design: `argparse` drives behavior. Add CLI flags for new features (e.g., `--mock`, `--partial-refresh`) and document them in `README.md`.

Developer workflows the agent should assume
- Local dev on non-Pi: run logic-only functions by mocking `waveshare_epd` imports or use `--mock` flag (suggest adding such a flag before creating tests). Do not instruct users to run the hardware init on CI runners.
- Install deps: `pip3 install -r requirements.txt` (also documented in `README.md`). The README includes `sudo python3 display_time.py` usage.
- Systemd deploy: the README shows a `/etc/systemd/system/eink-time.service` snippet — if asked to produce a service file, reuse that exact pattern and note `User=pi` is the conventional user.

Rules for code changes
- Keep changes minimal and easily reversible. This is a hardware demo; users prefer simple, auditable diffs.
- When adding tests, do not attempt to access the real device. Add a small shim or dependency-injection point so `epd2in8.EPD()` can be replaced with a mock in unit tests.
- Document any added CLI flags in `README.md` and include an example `systemd` change if it affects runtime args.

Files to reference when making changes
- `display_time.py` — main script and the most important file to read.
- `requirements.txt` — pinned runtime dependencies.
- `README.md` — install/run instructions and systemd example.

If you need more context
- Ask whether the target device supports partial refresh (this changes recommended update strategy).
- Ask whether the user wants 12h/24h localization, timezone handling, or additional overlays (weather, calendar).

Next step for maintainers
- If you'd like tests or CI, confirm an approach for mocking `waveshare_epd` and whether a `--mock` runtime flag is acceptable.

---
Please review this file and tell me if you'd like more details (examples of mocks/tests, partial-refresh implementation notes, or a refactor to separate rendering from device I/O).
