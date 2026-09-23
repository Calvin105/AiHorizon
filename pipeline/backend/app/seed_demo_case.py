"""A case that closes CONFIRMED, driven through the real HTTP API.

Run with the backend up:  uv run python -m app.seed_demo_case

Why this exists twice over:

1. **CONFIRMED is hard to reach by hand.** Step 8 needs all five conditions
   proved — a check confirmed the cause, exactly one thing was changed, the
   deciding signal was re-measured, it came back in spec, and it held. Most
   real runs stop short and close PLAUSIBLE, which is correct but means a
   demo has nothing to contrast against. This builds the other half of that
   contrast.

2. **It is the end-to-end test the suite doesn't have.** Every step goes
   through the same endpoints the frontend calls — no direct database
   writes — so a break anywhere between intake, vision, ranking, the loop
   and close makes this script fail. It exits non-zero if the case does not
   close CONFIRMED.

The photos are the project's own synthetic samples. `inconsistent.png`
measures size_cv ~0.49 against a `< 0.15` spec (gross); `good.png` measures
~0.05 (in spec). That before/after is what makes the close legitimate
rather than asserted.

The profile geometry is built from the sample's *own* ground-truth sidecar.
That is load-bearing: detect() matches a photo against the layout its
profile declares, so a profile whose geometry doesn't match the photo
fails the quality gate and the run degrades to answers only.
"""

import json
import sys
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8001/api"
REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLES = REPO_ROOT / "vision" / "samples"

DEFECT_PHOTO = SAMPLES / "inconsistent.png"
FIXED_PHOTO = SAMPLES / "good.png"
GEOMETRY_SIDECAR = SAMPLES / "good.json"

#: Marks what this script owns so a re-run replaces its own case.
DEMO_PROFILE_NAME = "Demo Grid 27G (matches sample photos)"

#: Occasional volume swings, random positions, cleared by a purge — the
#: fingerprint the brief's own worked example describes, and the one the
#: fault tree ranks air-in-fluid-path top for.
FINGERPRINT = {
    "axes": {
        "signature": ["size_varies"],
        "trajectory": "random",
        "footprint": "material",
        "inputs": ["new_lot_or_syringe"],
        "response": "purge_or_prime",
    },
    "signals": {},
    "axis_notes": {},
}

TARGET_CAUSE = "air_in_fluid_path"
SHOTS_HELD = 30


def step(n: int, text: str) -> None:
    print(f"\n[{n}] {text}")


def fail(message: str) -> None:
    print(f"\nFAILED: {message}")
    sys.exit(1)


def main() -> None:
    for path in (DEFECT_PHOTO, FIXED_PHOTO, GEOMETRY_SIDECAR):
        if not path.exists():
            fail(f"missing sample: {path}")

    client = httpx.Client(base_url=BASE_URL, timeout=60.0)
    try:
        client.get("/health").raise_for_status()
    except (httpx.HTTPError, OSError):
        fail(f"backend not reachable at {BASE_URL} — start it first.")

    # -- profile whose geometry matches the sample photos -----------------
    step(1, "Ensuring a profile whose geometry matches the sample photos")
    sidecar = json.loads(GEOMETRY_SIDECAR.read_text())
    geometry = {
        "pattern": "dots",
        "width": sidecar["width"],
        "height": sidecar["height"],
        "profile": sidecar["profile"],
    }

    profiles = client.get("/profiles", params={"limit": 200}).json()["items"]
    existing = next((p for p in profiles if p["name"] == DEMO_PROFILE_NAME), None)
    if existing:
        profile_id = existing["profile_id"]
        client.patch(f"/profiles/{profile_id}", json={"geometry": geometry}).raise_for_status()
        print(f"    reusing profile #{profile_id}")
    else:
        material_id = client.get("/materials", params={"limit": 1}).json()["items"][0]["material_id"]
        created = client.post(
            "/profiles",
            json={
                "name": DEMO_PROFILE_NAME, "material_id": material_id,
                "needle_gauge": "27G", "needle_id_um": 210,
                "set_pressure_kpa": 150, "set_time_ms": 120, "standoff_um": 300,
                "speed_mm_s": 25, "set_temp_c": 25,
                "spec_metric": "size_cv", "spec_limit": "< 0.15",
                "geometry": geometry,
            },
        )
        created.raise_for_status()
        profile_id = created.json()["profile_id"]
        print(f"    created profile #{profile_id} ({len(geometry['profile'])} dots)")

    station_id = client.get("/stations", params={"limit": 1}).json()["items"][0]["station_id"]

    # -- open the case ----------------------------------------------------
    step(2, "Opening the case")
    case = client.post(
        "/cases",
        json={
            "station_id": station_id, "profile_id": profile_id,
            "complaint": "Inconsistent size shot to shot",
            "complaint_text": (
                "Dot size is wandering shot to shot since the new syringe went in. "
                "It comes and goes rather than being wrong every time, and a purge "
                "seems to clear it for a while."
            ),
        },
    )
    case.raise_for_status()
    case_id = case.json()["case_id"]
    print(f"    case #{case_id}")

    # -- step 3: measure the defect --------------------------------------
    step(3, "Measuring the defect photo (inconsistent.png)")
    with DEFECT_PHOTO.open("rb") as fh:
        vision = client.post(
            f"/cases/{case_id}/vision",
            files={"photo": (DEFECT_PHOTO.name, fh, "image/png")},
        )
    vision.raise_for_status()
    v = vision.json()
    if not v["quality_ok"]:
        fail(f"quality gate rejected the defect photo: {v['quality_reason']}")
    print(f"    quality ok · magnitude={v['magnitude']} · size_cv={v['signals'].get('size_cv'):.3f}")

    # -- steps 1-2: the interview ----------------------------------------
    step(4, "Saving the interview answers")
    client.patch(f"/cases/{case_id}", json={"fingerprint": FINGERPRINT}).raise_for_status()
    print(f"    {FINGERPRINT['axes']}")

    # -- step 5: rank -----------------------------------------------------
    step(5, "Ranking the causes")
    ranking = client.post(f"/cases/{case_id}/rank")
    ranking.raise_for_status()
    r = ranking.json()
    for cause in r["pass1"][:3]:
        print(f"    {round(cause['likelihood'] * 100):>3}%  {cause['label']}")
    print(f"    tier {r['tier']}")

    # -- step 6: the loop. One look, then exactly one change. -------------
    step(6, "Logging an observation (costs the case nothing)")
    client.post(
        f"/cases/{case_id}/check-results",
        json={
            "check_name": "Hold the syringe up to the light", "cause_id": TARGET_CAUSE,
            "is_change": False, "outcome": "confirms",
            "result_detail": "Visible air slug about 4mm long sitting above the piston.",
        },
    ).raise_for_status()
    print("    looked — air slug seen")

    step(7, "Logging the one change the case is allowed")
    after_change = client.post(
        f"/cases/{case_id}/check-results",
        json={
            "check_name": "Purge the line, or swap in a fresh syringe", "cause_id": TARGET_CAUSE,
            "is_change": True, "outcome": "confirms",
            "result_detail": "Purged until bead ran clean, then re-primed. Dots came back even.",
        },
    )
    after_change.raise_for_status()
    top = after_change.json()["pass1"][0]
    print(f"    changed one thing — top cause now {top['label']} at {round(top['likelihood'] * 100)}%")

    # -- step 7: re-measure ----------------------------------------------
    step(8, f"Verifying with a fresh photo, held for {SHOTS_HELD} shots")
    with FIXED_PHOTO.open("rb") as fh:
        verify = client.post(
            f"/cases/{case_id}/verify",
            files={"photo": (FIXED_PHOTO.name, fh, "image/png")},
            data={"shots_measured": str(SHOTS_HELD)},
        )
    verify.raise_for_status()
    ver = verify.json()
    print(f"    {ver['signal']}: {ver['before']} -> {ver['after']:.3f} · in_spec={ver['in_spec']}")
    if not ver["in_spec"]:
        fail("re-measurement did not come back in spec — cannot close CONFIRMED.")

    # -- engineer notes ---------------------------------------------------
    step(9, "Adding engineer notes")
    client.patch(
        f"/cases/{case_id}",
        json={
            "engineer_notes": (
                "Air entrained when the syringe was changed — the barrel was not "
                "tapped down before loading. Worth adding a purge-and-inspect step "
                "to the syringe-change procedure."
            )
        },
    ).raise_for_status()

    # -- step 8: close ----------------------------------------------------
    step(10, "Closing the case")
    close = client.post(f"/cases/{case_id}/close")
    close.raise_for_status()
    result = close.json()
    print(f"    tier: {result['tier']}")
    for gap in result["gaps"]:
        print(f"    gap: {gap}")

    if result["tier"] != "CONFIRMED":
        fail(
            f"closed as {result['tier']}, not CONFIRMED. "
            "One of step 8's five conditions was not met — see the gaps above."
        )

    print(f"\nCONFIRMED. Case #{case_id}")
    print(f"  wizard  http://localhost:3001/troubleshoot/{case_id}")
    print(f"  case    http://localhost:3001/cases/{case_id}")
    print(f"  report  http://localhost:3001/cases/{case_id}/report")
    client.close()


if __name__ == "__main__":
    main()
