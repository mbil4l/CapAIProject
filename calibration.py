"""
Calibration inputs for Milestone 4: run both signals over the same texts and
print them side by side.

    python calibration.py

These five were invented for calibration, one per case that matters. They are
not my own writing, so they say nothing about criterion 1. They exist to see
where the signals agree and where they split.
"""

import config
import detector
import scoring
import stylometry

INPUTS = {
    "clearly AI": (
        "In today's rapidly evolving digital landscape, effective communication "
        "is essential for building successful teams. Organizations that "
        "prioritize collaboration are better positioned to achieve their goals. "
        "Furthermore, leveraging the right tools can significantly enhance "
        "productivity and foster innovation. It is important to note that clear "
        "expectations and regular feedback play a crucial role in employee "
        "engagement. By embracing these best practices, companies can create a "
        "more cohesive and resilient workplace."
    ),
    "clearly human": (
        "Honestly? I hated the first week at the bakery. Flour in my eyes, "
        "burnt thumb, and Mrs. Okafor yelling at me about the rye — which, fine, "
        "I did drop. By Friday though I could shape a loaf without thinking. "
        "Weird how that happens. Last night I caught myself kneading the air at "
        "a bus stop, like an idiot, and nobody even looked."
    ),
    "formal human": (
        "The committee's report, issued in March after eighteen months of "
        "hearings, concluded that the existing statute had failed to anticipate "
        "the consolidation of regional carriers. Its authors, while divided on "
        "remedy, agreed on diagnosis: enforcement had lagged the market, and the "
        "agency's discretionary powers, never intended to bear such weight, had "
        "been stretched past usefulness. Whether Parliament will act remains, as "
        "ever, uncertain."
    ),
    "lightly edited AI": (
        "In today's rapidly evolving digital world, good communication is "
        "essential for building succesful teams. Companies that prioritize "
        "collaboration are better placed to hit their goals. Using the right "
        "tools can really boost productivity. It's important to note that clear "
        "expectations and regular feedback play a big role in employee "
        "engagement. Embrace these practices, and companies can build a more "
        "cohesive workplace."
    ),
    # Same content as "clearly AI", but chopped into uneven sentences with more
    # punctuation. Built to make the style signal say "human" while the model
    # signal still says "AI" — the split the combining rule has to handle.
    "chopped AI": (
        "Communication matters. In a digital landscape that keeps evolving, "
        "teams that prioritize collaboration are simply better positioned to "
        "achieve their goals, and leveraging the right tools — which is "
        "important to note — can significantly enhance productivity. Feedback? "
        "Regular. Expectations? Clear. They play a crucial role in employee "
        "engagement; by embracing these best practices, companies can create a "
        "cohesive workplace."
    ),
    "plain human": (
        "I woke up late today. I made some coffee and checked my phone. Then I "
        "walked to the store to get milk and bread. The store was busy because "
        "it was Saturday. I came home and made a sandwich for lunch. After that "
        "I watched a movie with my brother."
    ),
}


def main():
    print(f"{'input':<18} {'model':>6} {'style':>6} {'combined':>9}   guess")
    for name, text in INPUTS.items():
        model = detector.model_signal(text)
        style = stylometry.style_signal(text)
        combined = scoring.combine_signals(model, style)
        guess, _ = scoring.score_to_label(combined)
        print(f"{name:<18} {model:>6.3f} {style:>6.3f} {combined:>9.3f}   {guess}")
    print()
    print(f"weights: model {config.WEIGHT_MODEL_SIGNAL}, style {config.WEIGHT_STYLE_SIGNAL}")
    print(f"bands:   {scoring.label_ranges()}")


if __name__ == "__main__":
    main()
