/** What a closed case actually asserts. Closing is not the same as fixing:
 * step 8 tiers on what was *proved*, so a case can close with the cause
 * pinned down and nothing repaired. The tier name alone reads like a
 * verdict on the repair, so the plain sentence is shown next to it. */
export const CLOSE_MEANING: Record<string, { headline: string; detail: string }> = {
  CONFIRMED: {
    headline: "Fixed and proved",
    detail:
      "A check confirmed the cause, exactly one thing was changed, and the deciding signal was " +
      "re-measured in spec and held. This is the only verdict that claims the fix worked, and the " +
      "only one that feeds future rankings.",
  },
  PLAUSIBLE: {
    headline: "Not proved fixed",
    detail:
      "Some of the five close conditions were met, but not all — so the case is a documented " +
      "lead, not a verified repair. It's shown to a human as context and adjusts nothing.",
  },
  UNVERIFIED: {
    headline: "Nothing proved",
    detail:
      "None of the five close conditions were met. The case is on file with what was tried, " +
      "and it adjusts nothing.",
  },
};

/** The "diagnosed" field in words: whether a check pinned the cause down. */
export const DIAGNOSED_WORDS: Record<string, string> = {
  check_confirmed: "Cause confirmed by a check",
  best_guess: "Best guess — no check confirmed it",
  never_tested: "Nothing tested yet",
};
