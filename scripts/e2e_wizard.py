"""Drive one case through the real UI in a browser, from photo to CONFIRMED.

    scripts/start-demo.sh                      # in another terminal
    uv run --with playwright python scripts/e2e_wizard.py [screenshot-dir]

The frontend's integration test: every step waits for the text that step is
supposed to produce, so a broken step fails loudly instead of screenshotting
an error. It opens the case over the API, then does everything else the way
an operator would — attach the photo, answer the interview and the
follow-up, log a look and one change, verify with a fresh photo, close —
and finally opens the printable report.

Uses Playwright's own Chromium (`uv run --with playwright playwright install
chromium`), or a system one via CHROMIUM_PATH=/usr/bin/chromium-browser.
Each run adds one case to the database; `python -m app.reset_demo` clears it.
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

APP = os.environ.get("APP_URL", "http://localhost:3001")
SAMPLES = Path(__file__).resolve().parents[1] / "vision" / "samples"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else None


def api(path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{APP}/api{path}", data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="GET" if body is None else "POST",
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def shot(page, name: str, full: bool = False) -> None:
    if OUT is None:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)


def chip(page, text: str) -> None:
    page.locator("button", has_text=text).last.click()


def main() -> None:
    profile = next(p for p in api("/profiles")["items"] if p["material"]["family"] == "epoxy")
    station = api("/stations")["items"][0]
    case_id = api("/cases", {
        "station_id": station["station_id"], "profile_id": profile["profile_id"],
        "complaint": "Inconsistent size shot to shot",
        "complaint_text": "Dot size wandering since the new syringe went in. Comes and goes; a purge clears it for a while.",
    })["case_id"]
    print(f"case #{case_id}")

    with sync_playwright() as p:
        executable = os.environ.get("CHROMIUM_PATH")
        browser = p.chromium.launch(executable_path=executable, headless=True) if executable else p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page.set_default_timeout(20000)

        page.goto(f"{APP}/troubleshoot/{case_id}")
        expect(page.get_by_text("can you photograph the deposits")).to_be_visible()
        page.locator('input[type="file"]').set_input_files(str(SAMPLES / "inconsistent.png"))
        expect(page.get_by_text(re.compile(r"Measured it — the deviation is"))).to_be_visible()
        shot(page, "01-photo-measured")

        page.locator("button", has_text="That's right").click()
        chip(page, "Random — comes and goes")
        chip(page, "The material")
        chip(page, "New lot or syringe just started")
        page.locator("button", has_text="Confirm").last.click()
        chip(page, "Purging or priming")

        expect(page.get_by_text(re.compile(r"Asked because"))).to_be_visible()
        shot(page, "02-follow-up")
        chip(page, "Steady at the set value")
        page.wait_for_timeout(1500)
        if page.get_by_text(re.compile(r"Asked because")).count() > 1:
            page.locator("button", has_text=re.compile(r"Random spots|Everywhere|Normal size")).last.click()

        expect(page.get_by_text(re.compile(r"leads because:"))).to_be_visible()
        shot(page, "03-ranking-why")

        chip(page, "Log a check")
        chip(page, "Air trapped in the syringe or material supply")
        chip(page, "Hold the syringe up to the light")
        chip(page, "Confirms it")
        page.get_by_placeholder(re.compile(r"air slug expelled")).fill("Air slug about 4 mm long above the piston.")
        page.locator("button", has_text="Log it").click()
        expect(page.get_by_text(re.compile(r"Logged — re-ranked"))).to_be_visible()
        shot(page, "04-check-reranked")

        chip(page, "Log a check")
        chip(page, "Air trapped in the syringe or material supply")
        chip(page, "Purge the line, or swap in a fresh syringe")
        chip(page, "Confirms it")
        page.locator("button", has_text="Log it").click()
        expect(page.get_by_text(re.compile(r"One change on the case so far"))).to_be_visible()

        chip(page, "Continue to report")
        expect(page.get_by_text("Want to verify the fix with a fresh photo?")).to_be_visible()
        page.locator('input[type="file"]').set_input_files(str(SAMPLES / "good.png"))
        chip(page, "50 or more")
        expect(page.get_by_text(re.compile(r"Everything the photo can check is back in spec"))).to_be_visible()
        chip(page, "Close the case")
        expect(page.get_by_text(re.compile(r"Closed as CONFIRMED"))).to_be_visible()
        shot(page, "05-closed-confirmed")

        page.goto(f"{APP}/cases/{case_id}/report")
        expect(page.get_by_text("Fix Verification")).to_be_visible()
        shot(page, "06-report", full=True)
        browser.close()

    print(f"OK — case #{case_id} driven through the UI to CONFIRMED")


if __name__ == "__main__":
    main()
