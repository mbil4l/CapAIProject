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

I run 10 things I wrote myself through it. No more than 1 may come back as
high-confidence AI, and none may score above 0.80. At least 4 of the 10 have to
be plain writing, short sentences and everyday words, since that's where the
model signal gets it wrong. It has to hold in all three trials, not just on
average.

**Why this target:** Telling someone their own work looks machine-made hurts
them a lot more than letting one AI paragraph through hurts the site. I'd like
to say zero, but gpt2 finds plain writing predictable and I can't promise it, so
I allow 1 in 10 and put a hard cap on how sure a wrong call can sound.


---

## 2. Clearly AI and clearly human text score apart (score spread)

I pick 5 pieces that are obviously AI and 5 that are obviously human. The AI
group's average combined score has to be at least 0.30 above the human group's
average. The lowest AI score also has to beat the highest human score, in all 3
trials.

**Why this target:** If the two groups overlap, the score means nothing. 0.30 is
about the width of one label band, so the groups should land in different bands.
I'm only asking that the easy cases are easy, not that every piece is sorted
right.


---

## 3. All three labels can actually be reached (label coverage)

Out of 10 test inputs, all three labels (human, unsure, AI) show up at least
once. `scoring.label_ranges()` shows no gap or overlap between the bands. The
unsure band is at least 0.25 wide. A score of 0.51 and a score of 0.95 get
different labels.

**Why this target:** A label nothing can produce is dead text, and one flip at
0.5 isn't confidence. The unsure band protects people the system can't judge, so
I want a minimum width on it, not just "it exists".


---

## 4. An appeal always changes status and is always recorded (appeal path)

I send 10 appeals using real `content_id`s from earlier submissions. All 10
return 200 with status `under_review`, and all 10 add an `appeal` entry to
`logs/audit.jsonl` with the writer's reasoning, next to the original decision.
The original entry never changes. An appeal with an unknown `content_id`, or
with blank reasoning, gets a 4xx and writes nothing.

**Why this target:** The appeal is all a wrongly flagged writer has, so it has to
work every time, which is why it's 10 of 10. Unknown ids get refused because
otherwise a typo looks like it worked and the writer thinks they were heard.


---

## 5. Bad input gets a clean refusal, never a crash (bad input)

I send 6 bad requests: no `text`, empty `text`, `text` that's only spaces,
`text` as `null`, `text` as a number, and a 50,000-word text. All 6 get a 400
(413 for the huge one) with a JSON `error` field. None gets a 500. All 6 leave a
`rejected` entry in the log. `/ping` still answers afterwards.

**Why this target:** A bad request that crashes the service is one of the most
common real failures, and a refusal that leaves no log entry can't be seen
later. It's 6 of 6 because each case is simple to handle.


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
