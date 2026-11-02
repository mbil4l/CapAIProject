# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. Own writing is rarely called AI (false positives)

Of 10 pieces I wrote myself, at most 1 is labeled high-confidence AI, and none
of the 10 has a combined score above 0.80. At least 4 of the 10 are in a plain
style (short sentences, everyday words), because that's the kind of writing the
model signal gets wrong. This has to hold in all three trials, not on average.

**Why this target:** On a writing site, telling someone their own work looks
machine-made costs them far more than letting an AI paragraph through costs the
site. I'd like to say zero, but with a 124M-parameter model that finds plain
writing predictable, I don't think I can promise it, so I'm allowing one in ten
and putting the harder cap on how confident a wrong call can be.


---

## 2. Clearly AI and clearly human text score apart (score spread)

Take 5 pieces that are obviously AI-written and 5 that are obviously
human-written. The average combined score of the AI group is at least 0.30
higher than the average of the human group, and the lowest AI score is still
higher than the highest human score in at least 3 of 3 trials.

**Why this target:** If the two groups sit on top of each other the score is
decoration. 0.30 is roughly the width of one label band, so the groups should
land in different bands. I'm not asking for perfect separation of every piece,
only that the easy cases are easy.


---

## 3. All three labels can actually be reached (label coverage)

Across a set of 10 test inputs, each of the three labels (human, unsure, AI)
shows up at least once, and `scoring.label_ranges()` shows no gap or overlap
between the bands. The "unsure" label covers at least 25% of the score range
(0.25 wide or more). Also, 0.51 and 0.95 must produce different labels.

**Why this target:** A label that no score can produce is dead text, and a
single flip at 0.5 isn't confidence. The unsure band has to be wide because it's
the label that protects people the system can't judge, so I want a minimum width
on it, not just "it exists".


---

## 4. An appeal always changes status and is always recorded (appeal path)

For 10 appeals sent with real `content_id`s from earlier submissions, 10 of 10
return 200 with status `under_review`, and 10 of 10 add an `appeal` entry to
`logs/audit.jsonl` with the writer's reasoning next to the original decision.
The original decision entry is never changed. An appeal with an unknown
`content_id`, or with blank reasoning, returns a 4xx and writes nothing.

**Why this target:** The appeal is the only thing a wrongly flagged writer has.
It should work every time, not most of the time, so the target is 10 of 10.
Refusing unknown ids matters because otherwise a typo looks like a success and
the writer thinks they've been heard.


---

## 5. Bad input gets a clean refusal, never a crash (bad input)

Send 6 bad requests: missing `text`, `text` as an empty string, `text` as only
whitespace, `text` as `null`, `text` as a number, and a 50,000-word text. All 6
return a 400 (or 413 for the huge one) with a JSON `error` field, none returns a
500, and all 6 leave a `rejected` entry in the log. The service still answers
`/ping` afterwards.

**Why this target:** A malformed request that crashes the service is the most
common real failure there is, and a refused request that leaves no log entry
is invisible. 6 of 6 because each of these is a single, easy case to handle.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
