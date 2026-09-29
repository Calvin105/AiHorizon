"""Step 3's quality gate (DESIGN.md W6): "too few deposits, low contrast, or
odd polarity means can't measure reliably, and the run continues on
questions only." This is upstream of everything else — a bad measurement
would otherwise fool both ranking passes into agreeing confidently.

detect() deliberately reports only silhouette geometry (see
vision/detect/classify.py's docstring) and no contrast/confidence score of
its own — segment.py already auto-corrects polarity and doesn't say
whether it had to. So this gate works from what *is* there: how many
regions were found at all, and how plausible their shapes are. It is a
proxy for "the image is unreadable," not a pixel-level contrast
measurement — documented here rather than overclaiming precision it
doesn't have.
"""

MIN_BLOBS = 2
DOT_SIZED_EXTRA = 0.25
"""An unmatched blob at least this fraction of a nominal deposit's area is
dot-sized: a pad, trace or marking, not a satellite or speck (those
measure a few % of a dot)."""
MAX_DOT_SIZED_EXTRAS = 2
MIN_MEAN_CIRCULARITY = 0.30
"""Real deposits, even defective ones, essentially never average below
this. A whole-frame value this low means Otsu most likely segmented noise,
not dots — the odd-polarity/low-contrast case."""


def quality_gate(cv_output: dict) -> tuple[bool, str | None]:
    """Returns (ok, reason). reason is None when ok."""
    if cv_output.get("error"):
        return False, cv_output["error"]

    washed_out = cv_output.get("image_quality", {}).get("washed_out_deposits", 0)
    if washed_out:
        # Glare lifts a deposit toward the white around it, so it reads as
        # undersized or missing on a good board — evaluation/ measured
        # 14-19% false alarms from strong glare before this check.
        return False, (
            f"Glare has washed out {washed_out} deposit(s) — they would read as undersized or missing "
            "when they may not be. Angle or diffuse the light, or lower the exposure, and retake."
        )

    if not cv_output.get("profile_supplied"):
        blobs = cv_output.get("blobs", [])
        if len(blobs) < MIN_BLOBS:
            return False, f"Only {len(blobs)} region(s) detected — too few to measure reliably."
        circularities = [b["circularity"] for b in blobs]
        mean_circ = sum(circularities) / len(circularities)
        if mean_circ < MIN_MEAN_CIRCULARITY:
            return False, "Detected regions are too irregular to be deposits — check focus/contrast."
        return True, None

    dots, extra = cv_output.get("dots", []), cv_output.get("extra", [])
    found = sum(1 for d in dots if d.get("area_ratio") is not None) + len(extra)
    if found < MIN_BLOBS:
        return False, f"Only {found} deposit(s) actually detected — too few to measure reliably."

    dot_sized = [e for e in extra if (e.get("area_ratio") or 0.0) >= DOT_SIZED_EXTRA]
    if len(dot_sized) >= MAX_DOT_SIZED_EXTRAS:
        # Clutter that touches a deposit also merges into it and distorts
        # its measured size and shape, so this is refused as a whole
        # rather than measured with the strays ignored.
        return False, (
            f"Found {len(dot_sized)} deposit-sized shapes that aren't in this profile's pattern — board "
            "features (pads, traces, markings) are being read as material. Crop to the dispense area or "
            "use a plainer background, and retake."
        )

    measured = [d for d in dots if "circularity" in d] + [
        {"circularity": 1.0} for _ in extra  # extras have no shape info; don't penalize them here
    ]
    circularities = [d["circularity"] for d in measured if "circularity" in d]
    if circularities:
        mean_circ = sum(circularities) / len(circularities)
        if mean_circ < MIN_MEAN_CIRCULARITY:
            return False, "Matched deposits are too irregular to be real — check focus/contrast/polarity."

    return True, None
