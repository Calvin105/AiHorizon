# INTRODUCTION

Good morning. We are Team Lithium, three of us are from USM and our project is DEFT. We are pursuing NSW Automation advanced level challenge and all 4 bonus challenges.


# PROBLEM

The problem starts with the new operator.

First, they don't know where to start.
As they are quite new, they have not developed the approaches to solve a particular problem. Say there are 5 causes to a problem, they are confused which one to start with and how to solve it.

Then, they solve it via trial-and-error, but they have changed the pressure, the needles.
Now they don't know which one actually solves it.

That experience tends to stay in senior engineers.
But they are siloed and their knowledge is not documented.

And simply giving them a confidence score doesn't solve the new operator's concerns.
How can they trust the score without knowing the cause?


# 3 CORE FEATURES

First let me familiarise DEFT with 3 core features:

First, a Knowledge Database. It documents each case by the 7 causes and 42 rules cited from NPL PDF, asking about the case from 5 different angles.

Second, our Dual-brain Ranking System where one brain check the factual inputs, another objects to it.

And third, a Senior Engineering Feedback System where junior ask senior help for troubleshooting.


# SOLUTION

Our solution is one guided troubleshooting session that remembers the past cases.

The operator takes a photo, answers 5 fixed observation questions and the system asks relevant follow-up questions that could actually change its diagnosis.

It then retrieves relevant cases to ranks top possible causes with confidence level and the why.

Now comes the troubleshooting part where a junior or senior may cut in to continue the case.

The operator starts with the top cause's check. Look first, then change one thing.
Every result goes back in, and the ranking updates live.

Stuck? They press Ask an engineer.

The case closes with a verdict and only proven verdict gets used in the future.


# THIRD-PARTY DECLARATION

Our causes and rules are cited from NPL Best Practice for Dispensing Report.

Our 2nd brain uses Groq free LLM API calls

We built using sqlite, opencv and next js.


# LIMITATIONS

4 limitations

One: fixed causes and rules
Two: image measured based on pixels not microns
Three: brain 2 is non-deterministic
Four: There may be look-alike causes






APPENDIX (backup slides, only if asked)

Three different questions, three different answers:
Quality score: how good are the dots?
Tier: how far can I trust the ranking?
Verdict: was the fix proved?


A1 · CONFIDENCE TIERS

```
HOW FAR TO TRUST THE RANKING

T1  Strong          A check confirmed the cause
                    or: no objection + pattern beats chance + 3+ matching confirmed cases, none disagreeing
T2  Provisional     No objection, but the measurement or the past cases don't back it yet
T3  Disagreement    Brain 2 objects, but the measurement keeps Brain 1's cause on top
T4  Don't force it  Brain 2 objects and nothing measured separates them → run the check

Every tier says why in one sentence. Agreement never raises a tier.
```

The tier tells the operator how far to trust the ranking.
T1 needs proof: either a check on the machine confirmed the cause, or Brain 2 has no objection, the measured pattern beats chance, and at least three matching confirmed cases back it.
If anything is missing, it's T2, provisional, and it says what's missing.
If Brain 2 objects, it drops to T3 or T4. T3 if the measurement still backs Brain 1. T4 if nothing separates them, so instead of picking one, it shows the check that settles it.

If asked "why doesn't agreement raise it?": two readers can make the same mistake, so agreement isn't proof.
If asked "Brain 2 objects but a check confirmed it?": still T1. A test on the machine outweighs a reading of the words.
If asked "what if there's no LLM?": Brain 2 doesn't run, which counts as no objection, not agreement.


A2 · VERDICTS (closing a case)

```
CLOSING A CASE IS NOT THE SAME AS FIXING IT

CONFIRMED   all 5 proved
            1  a check confirmed one cause
            2  exactly one change, aimed at it
            3  re-measured against a "before" photo
            4  back in spec
            5  held for 20+ shots
PLAUSIBLE   some proved   → shown as context, teaches nothing
UNVERIFIED  none proved   → teaches nothing

Every missing step is named, e.g. "3 things changed at once: no way to say which worked".
Only CONFIRMED cases become precedent for future rankings.
```

When a case closes, it gets a verdict.
CONFIRMED needs all five: a check confirmed one cause, exactly one change was made and aimed at it, the photo was re-measured against a before photo, it came back in spec, and it held for twenty shots.
Anything less is PLAUSIBLE or UNVERIFIED, and the record names what's missing.
Only CONFIRMED cases become precedent for the next operator, so a guess never gets taught to the system.

If asked "isn't T1 the same as CONFIRMED?": no. T1 is how sure the ranking is. CONFIRMED is proof the fix worked.


A3 · DISPENSING QUALITY SCORE (Bonus 2)

```
DISPENSING QUALITY SCORE: rates the dots, not the diagnosis
Example: a photo with scattered dot sizes

Completeness  ★★★★★  15 of 15 present
Size          ★☆☆☆☆   3 of 15 within 15% of the nominal size
Shape         ★★★★★  15 of 15 round
Position      ★★★★★  15 of 15 where the recipe puts them

Overall 20/100 = 3 of 15 dots passed all four
```

Bonus 2 is the dispensing quality score.
It rates the dots in the photo on four things: present, right size, round, in the right place.
Each gets stars, and a single failure always costs a star.
The overall score is the share of dots that pass all four, so here 3 of 15 is 20 out of 100.
Every number is a count you can check on the annotated photo.
It rates the dispensing, not the diagnosis. How far to trust the diagnosis is the tier's job.

If asked "why don't I see it?": it only shows when the photo passes the quality check and the job has a recipe, because without the recipe there are no positions to rate.


