"""
Signal two: the style signal.

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how many kinds?

Generated prose tends toward even, mid-length sentences and a narrower band of
vocabulary. Human writing is lumpier, with a three-word sentence next to a
forty-word one.

The blind spot: this signal cannot read. It has no idea what the text says.
Anything that changes the shape without changing the substance moves it —
typos, broken-up sentences, a pasted quotation. It also can't tell a person who
writes in short, even sentences on purpose from a model that does it by
default, and it's noisy on short text.

    python stylometry.py "some text to look at"
"""

import re
import statistics


# How the three measures turn into one 0–1 "more likely AI" score. Each raw
# measure is first mapped onto 0–1 (1 = looks machine-made), then these weights
# are applied. Sentence spread gets the most weight because it was the most
# separating measure on my calibration inputs (see calibration.py); word variety
# got the least because it separated almost nothing.
SPREAD_WEIGHT = 0.55
VARIETY_WEIGHT = 0.15
PUNCT_WEIGHT = 0.30

# Below this many sentences there is no honest spread to measure, so the spread
# part of the score is left neutral instead of guessing.
MIN_SENTENCES = 3

# A coefficient of variation at or above this counts as fully "human lumpy".
SPREAD_FULL = 0.60
# A moving type-token ratio at or above / below these counts as fully varied /
# fully repetitive.
VARIETY_HIGH = 0.95
VARIETY_LOW = 0.70
# Punctuation marks per word, and number of different kinds, that count as
# fully "human".
PUNCT_DENSITY_FULL = 0.14
PUNCT_KINDS_FULL = 5

TTR_WINDOW = 30


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


def _clamp(x: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, x))


# ── The three measures ───────────────────────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies: standard deviation of sentence lengths in
    words, divided by the mean, so long and short texts are comparable.

    Higher means lumpier, which reads as more human. Typical values run from
    about 0.1 (every sentence the same length) to 0.7 or more.

    Fewer than two sentences has no spread at all, so this returns 0.0 there.
    `style_signal` doesn't trust that 0.0, since it would mean "robotic" for
    what is really "no evidence".
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return statistics.stdev(lengths) / mean if mean else 0.0


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words, 0 to 1. Higher means more varied vocabulary.

    A plain ratio falls as text gets longer because common words keep
    repeating, so this averages the ratio over a sliding window of 30 words.
    That keeps a 60-word text and a 300-word text roughly comparable. Text
    shorter than one window just gets its plain ratio.
    """
    w = words(text)
    if not w:
        return 0.0
    if len(w) <= TTR_WINDOW:
        return len(set(w)) / len(w)
    ratios = [
        len(set(w[i:i + TTR_WINDOW])) / TTR_WINDOW
        for i in range(len(w) - TTR_WINDOW + 1)
    ]
    return sum(ratios) / len(ratios)


# Everything except the full stop. Full stops are in every text; these are the
# marks that differ from writer to writer. Apostrophes are left out because
# they're mostly contractions and possessives, not a style choice.
_PUNCT_KINDS = {
    "comma": r",",
    "semicolon": r";",
    "colon": r":",
    "dash": r"—|–|--|\s-\s",
    "parens": r"[()]",
    "quote": r"[\"“”]",
    "question": r"\?",
    "exclaim": r"!",
    "ellipsis": r"\.\.\.|…",
}


def punctuation_density(text: str) -> float:
    """
    Marks other than the full stop, per word. Higher means more punctuation.

    Commas, semicolons, colons, dashes, brackets, quotes, question and
    exclamation marks and ellipses all count. A text with no words returns 0.0.
    """
    n_words = len(words(text))
    if not n_words:
        return 0.0
    marks = sum(len(re.findall(p, text)) for p in _PUNCT_KINDS.values())
    return marks / n_words


def punctuation_kinds(text: str) -> int:
    """How many different kinds of punctuation show up at least once."""
    return sum(1 for p in _PUNCT_KINDS.values() if re.search(p, text))


# ── Combining them ───────────────────────────────────────────────────────────

def measures(text: str) -> dict:
    """The raw measures and what each one contributes, for printing and tests."""
    n_sent = len(sentences(text))
    spread = sentence_length_spread(text)
    ttr = type_token_ratio(text)
    density = punctuation_density(text)
    kinds = punctuation_kinds(text)

    # Each of these is 1.0 when that measure looks machine-made, 0.0 when it
    # looks human. Flipped from the raw numbers where higher meant "more human".
    if n_sent < MIN_SENTENCES:
        spread_ai = 0.5
    else:
        spread_ai = 1.0 - _clamp(spread / SPREAD_FULL)
    variety_ai = 1.0 - _clamp((ttr - VARIETY_LOW) / (VARIETY_HIGH - VARIETY_LOW))
    punct_human = 0.5 * _clamp(density / PUNCT_DENSITY_FULL) + 0.5 * _clamp(
        kinds / PUNCT_KINDS_FULL
    )
    punct_ai = 1.0 - punct_human

    return {
        "sentences": n_sent,
        "words": len(words(text)),
        "sentence_length_spread": round(spread, 3),
        "type_token_ratio": round(ttr, 3),
        "punctuation_density": round(density, 3),
        "punctuation_kinds": kinds,
        "spread_ai": round(spread_ai, 3),
        "variety_ai": round(variety_ai, 3),
        "punct_ai": round(punct_ai, 3),
    }


def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

    A weighted sum of three parts, each already pointing the same way as
    `detector.model_signal`:

        0.55 * spread_ai    even sentence lengths look machine-made
        0.15 * variety_ai   a narrow, repetitive vocabulary looks machine-made
        0.30 * punct_ai     sparse, uniform punctuation looks machine-made

    A text with fewer than three sentences gets a neutral 0.5 for the spread
    part instead of a guess.
    """
    m = measures(text)
    score = (
        SPREAD_WEIGHT * m["spread_ai"]
        + VARIETY_WEIGHT * m["variety_ai"]
        + PUNCT_WEIGHT * m["punct_ai"]
    )
    return round(_clamp(score), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    m = measures(text)
    print(f"{m['sentences']} sentences, {m['words']} words\n")
    print(f"sentence_length_spread   {m['sentence_length_spread']}   (higher = more human)")
    print(f"type_token_ratio         {m['type_token_ratio']}   (higher = more varied)")
    print(f"punctuation_density      {m['punctuation_density']}   ({m['punctuation_kinds']} kinds)")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
