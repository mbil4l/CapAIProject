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

Errors are always JSON, `{"error": "...", "message": "..."}`: a 400 for bad
input, a 413 for text over 20,000 characters, a 404 for an unknown
`content_id`, and a 503 if the model can't load. Nothing should ever be a 500.

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
| high-confidence human | below 0.35 | We think this was probably written by a person. Nothing in it looked machine-made to us, though no automatic check is perfect. |
| unsure | 0.35 to 0.65 | We can't tell whether this was written by a person or with an AI tool. That's not a finding that anything is wrong. Plain, short or heavily edited writing is hard for us to read either way. |
| high-confidence AI | above 0.65 | This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review. |

The bands are in `config.py` (`HUMAN_THRESHOLD = 0.35`, `AI_THRESHOLD = 0.65`)
and the label text is in `scoring.py` (`LABEL_HUMAN`, `LABEL_UNSURE`,
`LABEL_AI`). `scoring.label_ranges()` prints the bands and there's no gap
between them, so every score from 0 to 1 gets exactly one label. I reached all
three with real submissions (see Sample Run). The two bands that are easy to hit
are human and AI. Unsure took the "lightly edited AI" text.

**Why I worded the "unsure" one this way:** The person reading it may have
written every word, so the first thing it says is that we don't know, and the
second is that this isn't an accusation. I left out any number, and I said why
it's hard (plain, short or edited writing) so it doesn't read like a verdict on
them. I'm not sure it works. "Heavily edited" could read as a dig at someone who
did edit their work carefully, and I haven't tested these on anyone else yet.
The AI label says out loud that it can be wrong, since the false positive is the
mistake I care about most.


---

## Sample Run

The text I'm following here is a plain diary-style paragraph I invented to test
the false positive. It's not real writing from a real person. It gets
called AI, and then the "writer" appeals.

**A submission**

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "I woke up late today. I made some coffee and checked my phone. Then I walked to the store to get milk and bread. The store was busy because it was Saturday. I came home and made a sandwich for lunch. After that I watched a movie with my brother.", "creator_id": "sample_writer_4"}'
```

```json
{"confidence":0.7791,"content_id":"6a9666b702a2","guess":"ai","label":"This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.","model_score":0.8305,"status":"decided","style_score":0.7276}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "6a9666b702a2", "reasoning": "This is a plain diary entry I wrote myself. I write in short sentences."}'
```

```json
{"content_id":"6a9666b702a2","message":"We've got your appeal and marked this piece for review. The original result is kept as it was.","status":"under_review"}
```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log"
```

That returned 13 entries. These are the two for this `content_id`, picked out of
the full output (the rest are the other submissions and the rejections). The
log is append-only, so the original decision still says `decided` and the
appeal is written beside it. An item's current status is whatever its latest
entry says.

```json
{"combined_score": 0.7791, "content_id": "6a9666b702a2", "creator_id": "sample_writer_4", "guess": "ai", "label": "This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.", "model_score": 0.8305, "status": "decided", "style_score": 0.7276, "timestamp": "2026-11-02T07:34:43+00:00"}
{"content_id": "6a9666b702a2", "creator_id": "sample_writer_4", "event": "appeal", "reasoning": "This is a plain diary entry I wrote myself. I write in short sentences.", "status": "under_review", "timestamp": "2026-11-02T07:34:52+00:00"}
```

**The other label checks, from the same run**

| Text | model | style | combined | label |
|---|---|---|---|---|
| AI-style paragraph | 0.7697 | 0.5953 | 0.6825 | ai |
| bakery paragraph | 0.3119 | 0.0872 | 0.1996 | human |
| lightly edited AI | 0.7093 | 0.5281 | 0.6187 | unsure |

**Bad input and unknown ids** (criteria 4 and 5):

```
POST /submit  no text / "" / "   " / null / 42   ->  400 400 400 400 400
POST /submit  50,000 words                       ->  413
POST /appeal  content_id "6a9666b702zz" (typo)   ->  404 {"error":"unknown_content_id", ...}
POST /appeal  blank reasoning                    ->  400 {"error":"missing_reasoning", ...}
POST /ping    afterwards                         ->  {"ok":true,"service":"provenance-guard","you_sent":"hello"}
```

All of those leave a `rejected` entry in `logs/audit.jsonl`.

One thing that tripped me up on Windows: if the text has a character like an em
dash and I put it inline in `curl -d '...'`, it reaches the service in the wrong
encoding and I get `400 bad_json`. The service is right to refuse it. Sending the
same JSON from a file (`--data-binary @body.json`) works.

---

## How I Used AI

I used Claude Code for most of this unit: I gave it the brief and it wrote the
code, the README sections and the first draft of `criteria.md`. The brief tells
students not to have a model write their criteria. I told Claude to just write
them, so the five criteria and the numbers in them are its drafts, written
before it had seen any scores. Two specific moments:

**Moment 1**

- *What I asked for:* A second signal in `stylometry.py` built from sentence
  spread, word variety and punctuation.
- *What came back:* A working signal. Running it on six invented texts showed
  that the word-variety part pointed the wrong way: the AI paragraph had more
  variety than the human one. The plain "I woke up late today" paragraph also
  got called AI by both signals.
- *What I changed:* I kept word variety at the lowest weight (0.15) and wrote
  down that it separates almost nothing, instead of dropping it or tuning it
  until the table looked good. I also didn't move the thresholds to make the
  plain paragraph come out human, because that would be fitting to one example.
  It's listed as a known problem for unit 8.

**Moment 2**

- *What I asked for:* A sample run with one text for each label.
- *What came back:* The bakery text was refused with `400 bad_json` twice. First
  guess was a bug in the route.
- *What I changed:* Nothing in the service. Sending the identical JSON from a
  file worked, so the problem was Windows passing the inline curl argument in the
  wrong encoding. I used `--data-binary @file` for that one request and added a
  note to Sample Run.

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
