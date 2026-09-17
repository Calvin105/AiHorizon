"""Steps 1-2: the fixed question spine (DESIGN.md W3). Declared as data, not
endpoints or components, so the frontend renders one generic form from
whatever this module returns rather than hand-coding five screens."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionOption:
    value: str
    help_text: str = ""
    exclusive: bool = False
    """Selecting this clears every other selection on the same question —
    e.g. "Other / not sure", "Nothing unusual", "Don't know"."""


@dataclass(frozen=True)
class Question:
    id: str
    axis: str
    prompt: str
    kind: str  # "single" | "multi"
    options: list[QuestionOption]
    max_picks: int | None = None
    has_dont_know: bool = True
    has_other: bool = True


# Axis 1 lives with the defect picker (step 1) rather than the other four
# (step 2): the same option list is filled from the user's own pick *and*,
# later, from step 3's measurement, so it is asked here but scored as an
# axis like the rest.
IMAGE_ONLY_SIGNATURE_VALUE = "small_then_big"
"""Option 8 ('a small dot, then an oversized one') — the vocabulary holds
eight signature values but the picker exposes only the first seven; this
one can only be set by vision/service.py, and only above chance."""

SIGNATURE_OPTIONS = [
    QuestionOption("too_little", "starved, thin, under-filled"),
    QuestionOption("too_much", "oversized, flooded"),
    QuestionOption("size_varies", "some big, some small, no pattern"),
    QuestionOption("missing", "nothing came out at that point"),
    QuestionOption("shape_changes_across_board", "squat in one area, tall in another"),
    QuestionOption("wrong_shape", "tails, strings, satellites, voids, not round"),
    QuestionOption("spread_or_smeared", "looked right, then ran out of place"),
    # small_then_big (option 8) is image-only — vision/service.py sets it,
    # it is never offered in the picker.
]

QUESTIONS: list[Question] = [
    Question(
        id="signature",
        axis="signature",
        prompt="Compared with a good deposit, what is wrong with the bad one?",
        kind="multi",
        max_picks=2,
        options=SIGNATURE_OPTIONS,
    ),
    Question(
        id="trajectory",
        axis="trajectory",
        prompt="How has it behaved since it started?",
        kind="single",
        options=[
            QuestionOption("sudden_step", "Sudden, fine then bad from one point on"),
            QuestionOption("gradual", "Gradual, worse over hours or days"),
            QuestionOption("random", "Random, comes and goes"),
            QuestionOption("after_pause", "Only on the first shots after a pause"),
            QuestionOption("after_running_a_while", "Only after running a while"),
            QuestionOption("near_syringe_end", "Only near the end of a syringe"),
            QuestionOption("always_been_like_this", "It has always been like this"),
        ],
    ),
    Question(
        id="footprint",
        axis="footprint",
        prompt="If you move things around, what does the defect follow?",
        kind="single",
        options=[
            QuestionOption("material", "The material, it moves with the syringe or lot"),
            QuestionOption("tooling", "The nozzle, needle or valve"),
            QuestionOption("machine", "The machine or head"),
            QuestionOption("recipe", "The product or program"),
            QuestionOption("operator", "The shift or operator"),
            QuestionOption("everywhere", "Nothing, it happens everywhere"),
            QuestionOption("not_tested", "Not tested yet"),
        ],
    ),
    Question(
        id="inputs",
        axis="inputs",
        prompt="What is the state of the material and the supply right now?",
        kind="multi",
        options=[
            QuestionOption("fresh_lot", "Fresh lot, within pot life, thawed/degassed per spec"),
            QuestionOption("new_lot_or_syringe", "New lot or syringe just started"),
            QuestionOption("near_out_time", "Near or past out-time"),
            QuestionOption("syringe_nearly_empty", "Syringe nearly empty"),
            QuestionOption("ambient_changed", "Room temperature or humidity changed"),
            QuestionOption("air_supply_changed", "Air supply changed, wet, or recently serviced"),
            QuestionOption("nothing_unusual", "Nothing unusual", exclusive=True),
        ],
    ),
    Question(
        id="response",
        axis="response",
        prompt="What helps most, even temporarily?",
        kind="single",
        options=[
            QuestionOption("purge_or_prime", "Purging or priming"),
            QuestionOption("wipe_or_change_needle", "Wiping or changing the needle"),
            QuestionOption("new_syringe", "A new syringe"),
            QuestionOption("raise_pressure_or_time", "Turning pressure or shot time up"),
            QuestionOption("let_it_warm_up", "Letting it warm up"),
            QuestionOption("restart_or_rehome", "Restarting or re-homing"),
            QuestionOption("nothing_helps", "Nothing tried helps"),
            QuestionOption("not_tried", "Not tried yet"),
        ],
    ),
]

AXIS_WEIGHTS: dict[str, float] = {
    # "an axis is worth what it localises" — footprint/response are the
    # highest-yield questions, signature/inputs the lowest (DESIGN.md W5).
    "footprint": 1.5,
    "response": 1.5,
    "trajectory": 1.0,
    "signature": 0.7,
    "inputs": 0.5,
}


def question_by_id(question_id: str) -> Question | None:
    return next((q for q in QUESTIONS if q.id == question_id), None)
