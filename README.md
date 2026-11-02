# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

Provenance Guard is a small Flask service that looks at a piece of writing and
says how likely it is that a person wrote it. It never says "this is AI". It
says what it thinks and how sure it is, and it gives the writer a way to
disagree.

The path a submission takes:

1. **Arrives.** A client POSTs `{"text", "creator_id"}` to `/submit`.
2. **Route checks it.** `app.py::submit` rejects anything that isn't usable
   (no text, empty, not a string, too long) with a 400 and a log line, before
   any model runs.
3. **Signal one.** `detector.py` runs gpt2 on the text and turns its
   perplexity into a 0–1 score. This is the slow step, and the model stays
   loaded after the first call.
4. **Signal two.** `stylometry.py` measures the text's shape (sentence length
   spread, word variety, punctuation) and returns its own 0–1 score.
5. **Combine.** `scoring.py::combine_signals` turns the two scores into one
   combined score.
6. **Label.** `scoring.py::score_to_label` maps that score to one of three
   labels written for a normal reader.
7. **Log and answer.** `audit.py` appends the decision to `logs/audit.jsonl`
   with a new `content_id`, and the route returns it all as JSON. If the
   writer disagrees, `/appeal` finds that `content_id` in the log, records the
   appeal and flips the status to `under_review`.

### The two endpoints

`POST /submit`

| | Field | Notes |
|---|---|---|
| in | `text` | string, required, not blank |
| in | `creator_id` | string, required |
| out | `content_id` | short unique id, used later to appeal |
| out | `guess` | `ai`, `human` or `unsure` |
| out | `confidence` | the combined score, 0 to 1, higher means more likely AI |
| out | `label` | the sentence a reader sees |
| out | `model_score`, `style_score` | the two signals, each 0 to 1 |
| out | `status` | `decided` |

`POST /appeal`

| | Field | Notes |
|---|---|---|
| in | `content_id` | must already be in the log |
| in | `reasoning` | string, required, the writer's own words |
| out | `content_id`, `status` | status is now `under_review` |
| out | `message` | confirmation in plain language |

Errors are always JSON, `{"error": "...", "message": "..."}`, with a 400 for
bad input and a 404 for an unknown `content_id`. Nothing should ever be a 500.

### The false positive I'm designing around

A real writer, say someone writing in their second language, sends in a plain
paragraph made of short sentences and everyday words. gpt2 finds that very
predictable, so signal one scores it high. Their sentences are all about the
same length, so signal two agrees. The combined score comes out high, and
they'd see the "probably AI" label on work they wrote themselves. They can
send an appeal with the `content_id` and their reasoning, and it goes to
`under_review`. Nobody re-checks it automatically, so a human has to pick it
up. That's why the AI threshold sits high and the unsure band is wide.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to gpt2, running on my own
machine (`detector.py::model_signal`). It takes the perplexity, which is how
surprised the model is by each next word, and squashes it onto 0–1 so that low
perplexity gives a high AI score.

**Why that might differ between human and AI writing:** A language model
writes by picking likely next words, so its output is easy for another model
to predict. People reach for odd words and sudden turns more often.

**What it can't see:** Authorship. Predictable is not the same as machine
written. Plain writing in short sentences and common words, from a second
language speaker, a younger writer or anyone being deliberately simple, scores
as machine-like. Dense, ornate human prose with rare words can score as human
even when an AI wrote it. It also only reads the first 400 tokens.

### Signal two — the style signal

**What it measures:** The shape of the text without reading it
(`stylometry.py::style_signal`): how much sentence length varies, how many
different words there are compared with the total, and how much punctuation
there is and how varied it is.

**Why that might differ between human and AI writing:** Generated prose tends
to have even, mid-length sentences and a narrower vocabulary. Human writing is
lumpier, with a three-word sentence right next to a forty-word one.

**What it can't see:** Meaning. It has no idea what the text says, so anything
that changes the shape and not the content moves it: typos, chopping sentences
up, pasting in a quotation. Those are cheap to do on purpose. It is also
unreliable on short text, where a few sentences give a noisy spread.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** Take a weighted average of the two signals. If they disagree by
more than a set gap, pull the average halfway back toward 0.5. Two methods that
disagree are telling me they don't know, and the label should say so. I'm not
making the average lean toward either signal, because on my calibration texts
neither was clearly the more trustworthy one. The one place I worried about it
is that agreement can't be fixed by a rule: when both signals are wrong in the
same direction (plain human writing), the average is wrong too.

**The numbers:** `WEIGHT_MODEL_SIGNAL = 0.5`, `WEIGHT_STYLE_SIGNAL = 0.5`,
`DISAGREE_GAP = 0.30`, `DISAGREE_SHRINK = 0.5` (all in `config.py`). Inside
the style signal, the weights are 0.55 for sentence length spread, 0.30 for
punctuation and 0.15 for word variety (`stylometry.py`). Word variety gets the
least because on my calibration texts it separated almost nothing. The AI text
had *more* variety than the human text.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

The six calibration inputs in `calibration.py` (all invented for this, none is
my own writing), with both signals and the combined score:

```
input               model  style  combined   guess
clearly AI          0.770  0.595     0.682   ai
clearly human       0.312  0.087     0.200   human
formal human        0.315  0.174     0.244   human
lightly edited AI   0.709  0.528     0.619   unsure
chopped AI          0.448  0.032     0.370   unsure
plain human         0.831  0.728     0.779   ai
```

The split is "chopped AI": the same content as "clearly AI", broken into
uneven sentences with more punctuation. The style signal read it as human
(0.03) and the model signal sat in the middle (0.45). That's a gap of 0.42. A
plain average gives 0.24, which would be labeled human, so the AI text gets
through with a confident label. The rule sees the gap is over 0.30 and pulls
the score back to 0.37, which is "unsure". It still gets through, but it
doesn't get a stamp of approval.

Two things in that table I'm not happy about:

- **Plain human is called AI.** A short paragraph of ordinary sentences
  ("I woke up late today. I made some coffee...") scores 0.83 on the model
  signal and 0.73 on style, so both agree and the combined score is 0.78. That
  is the false positive from Milestone 1, showing up in the very first
  calibration run. No combining rule fixes two signals agreeing on the wrong
  answer. I'm leaving the thresholds where they are rather than moving them
  until this one text comes out right, since I'd be fitting to one example. It's
  the first thing unit 8 should look at.
- **The margin on "clearly AI" is thin.** 0.68 against an AI threshold of 0.65.


---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "creator_id": "..."}'
```

```json

```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json

```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
