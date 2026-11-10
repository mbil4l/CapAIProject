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
- **The margin on "clearly AI" is thin.** 0.68 against an AI threshold of 0.65
  (at the time of unit 7; unit 8 moved it to 0.72, see The Improvement).


---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | below 0.35 | We think this was probably written by a person. Nothing in it looked machine-made to us, though no automatic check is perfect. |
| unsure | 0.35 to 0.72 (was 0.65 in unit 7) | We can't tell whether this was written by a person or with an AI tool. That's not a finding that anything is wrong. Plain, short or heavily edited writing is hard for us to read either way. |
| high-confidence AI | above 0.72 (was 0.65 in unit 7) | This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review. |

The bands are in `config.py` (`HUMAN_THRESHOLD = 0.35`, `AI_THRESHOLD = 0.72`, changed in unit 8)
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

I used an AI coding assistant for most of this unit: I gave it the brief and it wrote the
code, the README sections and the first draft of `criteria.md`. The brief tells
students not to have a model write their criteria. I told it to just write
them, so the five criteria and the numbers in them are its drafts, written
before it had seen any scores. After that I had it reword them in plainer
language, with every number left the same. Two specific moments:

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

**Unit 8**

The AI assistant did the work for this unit too: the rate limiter, the attack
run, `scenarios.py`, the verdicts, the fix and the write-up. Two moments, plus
one thing I should be plain about.

**Moment 3**

- *What I asked for:* Ten pieces of my own writing for criterion 1. I didn't
  have them to hand, and I asked the assistant to write them in a junior
  developer's voice.
- *What came back:* Ten short pieces in `my_writing.txt`, six of them plain.
- *What I changed:* Nothing in the pieces, but the file's header and the Run Log
  both say they are stand-ins written by the assistant, and criterion 1's
  verdict and the fix are described as measured on them. That makes the
  criterion 1 result weaker than a real one would be, and the README says so.

**Moment 4**

- *What I asked for:* A diagnosis of why each broken attack broke.
- *What came back:* A first draft that said PI02's low style score came from
  punctuation variety, and that the Arabic text (MF07) scored as AI because of
  "byte-level tokens". Both were guesses.
- *What I changed:* I had them checked before keeping them. PI02's style score
  actually came from sentence-length spread (0.65), because the fake header adds
  short sentences next to long ones; punctuation wasn't the cause. For MF07,
  gpt2 really does produce about one token per character (103 for 105), so that
  part held up. I corrected the PI02 text and added the token count.

I also let the assistant's judge for criterion 4 stay strict. It counted the
two `rejected` log lines from refused appeals as a failure of "writes nothing".
That cost me a MISSED I could have argued away.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 50 per day (`RATE_LIMIT_PER_MINUTE` and
`RATE_LIMIT_PER_DAY` in `config.py`, applied to `POST /submit`).

**Why those numbers and not others:** A real writer sends a draft, reads the
label, fixes something and sends it again. That's a handful of requests in a
few minutes, so 5 a minute doesn't get in their way, and 50 a day is more than a
full working session. A script trying to map my thresholds needs hundreds or
thousands of probes with small edits between them. At 50 a day it gets 50 data
points a day from one creator_id, which is slow enough to be annoying but
doesn't stop it. I didn't go lower because a limit that blocks a writer who is
revising is worse than one that only slows a script, and a false accusation on a
rushed rewrite is the thing I'm trying to avoid in the first place. I also
didn't go much higher because every request runs gpt2, which is the expensive
part of the service.

**What a caller counts as:** The `creator_id` in the request body. If there
isn't a usable one (a malformed body, a bare list), it falls back to the
caller's IP address. That's the starter's `rate_limit_key` in `app.py`, which I
left as it was. The weak spot is obvious: a script that makes up a new
creator_id for every request never hits a limit, and the attack set does exactly
that. Counting by address instead would catch that script but would also lump a
whole household or school together as one writer. I haven't built a
combination of the two.

**The run of status codes when I pushed past it:**

```
$ python run_attacks.py --flood 15
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

10 of 15 were rate limited. `GET /health` reported `"rate_limiting": true`, and
the rejections are in the audit log as entries with `"reason": "rate_limited"`
and `"limit": "5 per 1 minute"`. The raw run is in
`results/flood_2026-11-10_0400.md`.

---

## Attack Run — Before

56 attacks, run with `python run_attacks.py --set . --label before`, against the
service as committed at the end of Milestone 1 (rate limiting on, 5 a minute).
Nothing was changed between that commit and this run. The full output is
`results/attack_run_2026-11-10_0405_before.md`, with my verdict filled in for
every row.

**How I decided held or broke.** Whether an attack worked depends on where my
thresholds sit, so I wrote the rule down before marking anything:

- An evasion or injection attack is aimed at AI-written text. It **broke** if
  the text didn't get the AI label, and it broke worst if it got the human one.
  "Unsure" doesn't count as caught. The point of the attack was to avoid the
  AI label, and it did.
- A false-positive attack is real human writing. It **broke** only if it got the
  AI label. "Unsure" held, because nobody was accused.
- A malformed attack **broke** if it crashed the service or if junk that isn't
  writing got a decision. A clean 4xx held.
- A flood attack **held** if the limit cut in.

**Result: 16 broke, 40 held, no crashes (no 500s anywhere).**

| Family | Attacks | Broke | Held |
|---|---|---|---|
| evasion | 10 | 10 | 0 |
| false_positive | 8 | 3 | 5 |
| prompt_injection | 6 | 1 | 5 |
| malformed | 20 | 2 | 18 |
| flood_same_creator | 12 | 0 | 12 |

| ID | Family | What it was going for | Status | Label | Score | Verdict |
|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | unsure | 0.450 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.460 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.480 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | unsure | 0.617 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.265 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.456 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.479 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | unsure | 0.455 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.512 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | unsure | 0.634 | BROKE |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | unsure | 0.527 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | ai | 0.692 | BROKE |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | ai | 0.700 | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 | unsure | 0.584 | HELD |
| FP05 | false_positive | technical documentation written by a person | 200 | ai | 0.743 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.571 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | unsure | 0.566 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | unsure | 0.388 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | unsure | 0.389 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.200 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.506 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | unsure | 0.449 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | unsure | 0.494 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | unsure | 0.505 | HELD |
| MF01 | malformed | text is only whitespace | 400 | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | — | — | HELD |
| MF03 | malformed | text is control characters | 400 | — | — | HELD |
| MF04 | malformed | text is only punctuation | 200 | unsure | 0.465 | BROKE |
| MF05 | malformed | text is a very long single word | 400 | — | — | HELD |
| MF06 | malformed | text is emoji only | 400 | — | — | HELD |
| MF07 | malformed | text is right-to-left script | 200 | ai | 0.816 | BROKE |
| MF08 | malformed | text is 60,000 characters | 413 | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | — | — | HELD |
| RQ05 | malformed | text is null | 400 | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |

Two rows need a note. RQ10 and RQ11 came back 429 instead of 400. They never
reached my route: the address-wide bucket had already been used up by the
earlier malformed rows that carried no usable `creator_id`, and a rejected
request still counts against the limit. They left a `rate_limited` entry in the
log, so I marked them held, but it does mean a run of malformed requests from
one address locks that address out of `/submit`, honest writer or not.

**Ten audit log entries from the run**

These are the failures, not the easy ones: FP03, FP05, EV05, PI02, MF07, MF04,
EV10, FP01 and PI05 in that order, then one rate-limit rejection (the last line,
a 429 that never reached the route, so it has fewer fields). The same ten are in
`results/audit_extract_before.jsonl`.

```json
{"timestamp": "2026-11-10T09:05:37+00:00", "content_id": "5743ceb998e8", "creator_id": "attacker_FP03", "guess": "ai", "model_score": 0.8051, "style_score": 0.594, "combined_score": 0.6996, "label": "This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.", "status": "decided", "text_chars": 418, "text_hash": "f876400f145c"}
{"timestamp": "2026-11-10T09:05:37+00:00", "content_id": "160ff8816b7d", "creator_id": "attacker_FP05", "guess": "ai", "model_score": 0.8005, "style_score": 0.6859, "combined_score": 0.7432, "label": "This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.", "status": "decided", "text_chars": 393, "text_hash": "7545ded55342"}
{"timestamp": "2026-11-10T09:05:37+00:00", "content_id": "95f7d25fd253", "creator_id": "attacker_EV05", "guess": "human", "model_score": 0.3212, "style_score": 0.208, "combined_score": 0.2646, "label": "We think this was probably written by a person. Nothing in it looked machine-made to us, though no automatic check is perfect.", "status": "decided", "text_chars": 460, "text_hash": "a20f4a78c4a5"}
{"timestamp": "2026-11-10T09:05:38+00:00", "content_id": "91e307cee817", "creator_id": "attacker_PI02", "guess": "human", "model_score": 0.2044, "style_score": 0.1961, "combined_score": 0.2002, "label": "We think this was probably written by a person. Nothing in it looked machine-made to us, though no automatic check is perfect.", "status": "decided", "text_chars": 322, "text_hash": "61f8f3b0b0b9"}
{"timestamp": "2026-11-10T09:05:38+00:00", "content_id": "e47f6f10e849", "creator_id": "attacker_MF07", "guess": "ai", "model_score": 0.9064, "style_score": 0.725, "combined_score": 0.8157, "label": "This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.", "status": "decided", "text_chars": 105, "text_hash": "1871a57b4854"}
{"timestamp": "2026-11-10T09:05:38+00:00", "content_id": "a1c009bbb75c", "creator_id": "attacker_MF04", "guess": "unsure", "model_score": 0.0112, "style_score": 0.85, "combined_score": 0.4653, "label": "We can't tell whether this was written by a person or with an AI tool. That's not a finding that anything is wrong. Plain, short or heavily edited writing is hard for us to read either way.", "status": "decided", "text_chars": 31, "text_hash": "66eb457f9df7"}
{"timestamp": "2026-11-10T09:05:37+00:00", "content_id": "226d9e308d73", "creator_id": "attacker_EV10", "guess": "unsure", "model_score": 0.9792, "style_score": 0.5587, "combined_score": 0.6345, "label": "We can't tell whether this was written by a person or with an AI tool. That's not a finding that anything is wrong. Plain, short or heavily edited writing is hard for us to read either way.", "status": "decided", "text_chars": 544, "text_hash": "efb8495d3ad8"}
{"timestamp": "2026-11-10T09:05:37+00:00", "content_id": "104bea2e7976", "creator_id": "attacker_FP01", "guess": "unsure", "model_score": 0.6175, "style_score": 0.4359, "combined_score": 0.5267, "label": "We can't tell whether this was written by a person or with an AI tool. That's not a finding that anything is wrong. Plain, short or heavily edited writing is hard for us to read either way.", "status": "decided", "text_chars": 523, "text_hash": "dbb48651b55f"}
{"timestamp": "2026-11-10T09:05:38+00:00", "content_id": "18cc9d21b01a", "creator_id": "attacker_PI05", "guess": "unsure", "model_score": 0.6401, "style_score": 0.335, "combined_score": 0.4938, "label": "We can't tell whether this was written by a person or with an AI tool. That's not a finding that anything is wrong. Plain, short or heavily edited writing is hard for us to read either way.", "status": "decided", "text_chars": 213, "text_hash": "6dc8b1a2a806"}
{"timestamp": "2026-11-10T09:05:38+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

FP03, the "non-native English speaker writing carefully": *"I want to describe my
experience of the first month in this country. The weather was very different
from my home. I did not expect the rain to continue for so many days..."* My
service answered `guess: ai`, `confidence: 0.6996`, with model_score 0.8051 and
style_score 0.594, and the label that says it "looks like it may have been
written with an AI tool." This is the person I traced in Milestone 1 of the last
unit, and it happened exactly the way I described it. Writing carefully in
plain words is what both of my signals read as machine-made, and that writer has
the least room to argue. The appeal path would move it to `under_review`, but
nothing re-checks it after that, so the accusation just sits there.

---

## Run Log and Verdicts

Five criteria from `criteria_unit7.md` (the unit 7 file; `criteria.md` was
later reused by the capstone), three trials each, **before** the fix. Produced by
`run_eval.py --label before` against `scenarios.py`; the full output is
`results/run_2026-11-10_0510_before.md`. All three trials came out identical for
every criterion, which is what I expected, since nothing in either signal is
random.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Own writing is rarely called AI | 1 of 10 at most, none above 0.80, 4+ plain | 2/10 flagged, top 0.71 (FAIL) | 2/10 flagged, top 0.71 (FAIL) | 2/10 flagged, top 0.71 (FAIL) | MISSED |
| 2. Clearly AI and clearly human score apart | gap 0.30+, lowest AI above highest human | gap 0.43, 0.60 vs 0.39 (pass) | gap 0.43, 0.60 vs 0.39 (pass) | gap 0.43, 0.60 vs 0.39 (pass) | MET |
| 3. All three labels reachable | 3 of 3, unsure band 0.25+, 0.51 and 0.95 differ | 3/3, band 0.30, differ (pass) | 3/3, band 0.30, differ (pass) | 3/3, band 0.30, differ (pass) | MET |
| 4. An appeal always changes status and is recorded | 10 of 10, refused appeals write nothing | 10/10 ok, but 2 log lines written (FAIL) | 10/10 ok, but 2 log lines written (FAIL) | 10/10 ok, but 2 log lines written (FAIL) | MISSED |
| 5. Bad input refused cleanly | 6 of 6, none 500, all 6 logged, ping ok | 6/6, 0 crashed, 6/6 logged (pass) | 6/6, 0 crashed, 6/6 logged (pass) | 6/6, 0 crashed, 6/6 logged (pass) | MET |

**Two things about how I got these numbers.**

- **Criterion 1 was measured on stand-ins, not my writing.** The ten pieces in
  `my_writing.txt` were written by the AI assistant in a junior developer's voice
  (the file says so at the top), because I hadn't supplied ten pieces of my own.
  Six of them are plain (short sentences, everyday words), four aren't. So
  criterion 1's verdict is for those ten pieces. A real number needs real
  writing, and I'd re-run it with that.
- **I extended `run_eval.py`.** It only sent text and printed labels. Criteria 4
  and 5 need a submission followed by an appeal, and a look in the log, so
  scenarios can now carry their own `runner` and a `judge` that applies the
  target to each trial. The service wasn't touched.

**How I decided the two misses.** Criterion 1 says at most 1 of 10; every trial
had 2 (pieces 1 and 10). That is a miss however it's read. Criterion 4 is the
one I thought about. All 10 appeals worked: 200, status `under_review`, an
appeal entry with the reasoning, and the original decision still `decided`. The
criterion also says a refused appeal "writes nothing". The two refused ones (an
unknown `content_id` and blank reasoning) wrote no appeal, but each wrote a
`rejected` line to the log. The generous reading is that "nothing" meant no
appeal record. The words say nothing, and I wrote them. So I'm calling it
MISSED. I'm not revising the criterion either: it can be measured, I just broke
it, and that's the case the brief says doesn't count as a revision. The real
issue is that it conflicts with a decision I made in Milestone 1, to log every
refusal, which I'd still keep.

**Real output from trial 1**, one block per criterion. Each line is one real
response object from `results/run_2026-11-10_0510_before.md`, trimmed to the
entries that show the point.

Criterion 1, `scenarios.py::judge_own_writing` over pieces 1 and 10 (the two
flagged):

```json
{"status": 200, "guess": "ai", "confidence": 0.6983, "model_score": 0.6369, "style_score": 0.7596, "label": "This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.", "sent": "Today I fixed the bug in the login form. The error showed up when the "}
{"status": 200, "guess": "ai", "confidence": 0.7065, "model_score": 0.6218, "style_score": 0.7912, "label": "This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.", "sent": "I wrote a script to rename the log files. It reads the folder and adds"}
```

Criterion 2, `scenarios.py::judge_spread`, the first AI text and the first human
text:

```json
{"status": 200, "guess": "ai", "confidence": 0.7326, "model_score": 0.8337, "style_score": 0.6314, "label": "This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.", "sent": "In today's fast-paced world, time management has become an essential s"}
{"status": 200, "guess": "unsure", "confidence": 0.3942, "model_score": 0.533, "style_score": 0.0439, "label": "We can't tell whether this was written by a person or with an AI tool. That's not a finding that anything is wrong. Plain, short or heavily edited writing is hard for us to read either way.", "sent": "My brother borrowed the van in March and I haven't seen it since. He s"}
```

Criterion 3, `scenarios.py::judge_coverage`, one response for each label:

```json
{"status": 200, "guess": "ai", "confidence": 0.7326, "model_score": 0.8337, "style_score": 0.6314, "label": "This looks like it may have been written with an AI tool. We can be wrong, especially about plain or simple writing. If you wrote it yourself, tell us using the appeal option and we'll mark it for review.", "sent": "In today's fast-paced world, time management has become an essential s"}
{"status": 200, "guess": "unsure", "confidence": 0.603, "model_score": 0.8821, "style_score": 0.5298, "label": "We can't tell whether this was written by a person or with an AI tool. That's not a finding that anything is wrong. Plain, short or heavily edited writing is hard for us to read either way.", "sent": "Regular exercise offers a wide range of benefits for both physical and"}
{"status": 200, "guess": "human", "confidence": 0.253, "model_score": 0.3187, "style_score": 0.1873, "label": "We think this was probably written by a person. Nothing in it looked machine-made to us, though no automatic check is perfect.", "sent": "We never did fix the gate. It dragged on the gravel every single time,"}
```

Criterion 4, `scenarios.py::run_appeals` and `judge_appeals`, the first
appeal and the log check after the two refused ones:

```json
{"sent": "In today's fast-paced world, time management has become an e", "submit_status": 200, "content_id": "e6349dda9467", "reasoning": "eval appeal 1: I wrote this myself.", "appeal_status": 200, "appeal_body_status": "under_review", "decision_entries": 1, "decision_still_decided": true, "appeal_entries": 1, "appeal_recorded": true}
{"negative": "log after the two refused appeals", "appeal_entries_added": 0, "entries_added": 2, "entries": [{"content_id": "eval_no_such_id", "creator_id": "unknown", "event": "rejected", "reason": "unknown_content_id", "status": "rejected", "timestamp": "2026-11-10T10:10:41+00:00"}, {"creator_id": "unknown", "event": "rejected", "reason": "missing_reasoning", "status": "rejected", "timestamp": "2026-11-10T10:10:41+00:00"}]}
```

Criterion 5, `scenarios.py::run_bad_input` and `judge_bad_input`, the six
bad requests and the check afterwards:

```json
{"sent": "eval_bad_missing: text='<absent>'", "status": 400, "error": "bad_text"}
{"sent": "eval_bad_empty: text=''", "status": 400, "error": "text_too_short"}
{"sent": "eval_bad_spaces: text='   '", "status": 400, "error": "text_too_short"}
{"sent": "eval_bad_null: text='None'", "status": 400, "error": "bad_text"}
{"sent": "eval_bad_number: text='42'", "status": 400, "error": "bad_text"}
{"sent": "eval_bad_huge: text='word word word word '", "status": 413, "error": "text_too_long"}
{"after": true, "rejected_entries_added": 6, "ping_status": 200, "ping_ok": true}
```

**Diagnoses**

*Criterion 1 missed, and FP02 and FP03 from the attack set (stage: signal two,
with signal one agreeing).* Pieces 1 and 10 are plain: five short sentences of
similar length, no commas, no punctuation except full stops. Signal two scored
them 0.76 and 0.79. Its sentence-spread part reads even sentences as
machine-like (0.61 and 0.71), and its punctuation part gives 1.0, the maximum,
to text with no marks other than full stops. Signal one gave 0.64 and 0.62, which
is high but under the line on its own. The two agree (a gap well under 0.30), so
the combining rule's disagreement shrink never fired, and the average, 0.698 and
0.7065, went over 0.65. If signal two had said a neutral 0.5 the averages would
have been about 0.57 and 0.56, both unsure. So signal two decided it. The
pattern is wider than those two pieces: 5 of my 6 plain pieces scored 0.50 or
more, and none of the four other pieces did (highest 0.48). That is the blind
spot I wrote about before building anything, showing up in a count. FP02 (formal
report, 0.692) and FP03 (careful second-language writer, 0.700) are the same
thing, both signals agreeing, and the label mapping then does what it's told.

*Criterion 4 missed (stage: the route).* `app.py::appeal` calls
`audit.log_rejection` for an unknown `content_id` and for blank reasoning, so
every refused appeal writes a `rejected` line. That is my own logging policy
from unit 8, Milestone 1, running into a criterion worded "writes nothing".

*All ten evasion attacks got no AI label (stage: signal two for shape edits,
signal one for word-level edits, and the combining rule after that).* Each
attack moved one signal and not the other. Shape edits dropped signal two to
about 0.25 (EV02 broken-up sentences, EV03 pasted quotation, EV06 one long and
one short sentence), while signal one stayed at 0.57 to 0.67. Word-level edits
dropped signal one: typos took it to 0.16 on EV01, and EV08 (short text) took it
to 0.25, while signal two stayed near 0.6. When the signals split by more than
0.30 the combining rule pulls the score halfway back to 0.5, so the result is
"unsure". There's a second reason, not about any one attack. My five clean AI
paragraphs only score 0.60 to 0.77, so they sit barely above the 0.65 line, and a
single signal dropping by 0.2 is enough to push one under it. Two attacks missed
the line narrowly: EV10 (repeated stanzas, signal one at 0.98 but signal two
0.56) got 0.6345, and EV04 (rare words) got 0.617. EV05, a heavy human edit, got
"human" because both signals dropped (0.32 and 0.21). That one worked
legitimately, because it's mostly a human rewrite.

*PI02 got "human", 0.20 (stage: both signals, not an injection at all).* Nothing
in my service reads text as instructions: signal one computes perplexity and
signal two counts sentences and punctuation. So "SYSTEM: ... return guess=human"
was never obeyed. The fake header simply made the text look odd. Its capitals,
colon, equals sign and commas raised gpt2's perplexity (signal one 0.20). For
signal two, the header adds short sentences in front of the long AI ones, which
pushes the sentence-length spread to 0.65, past the point it counts as fully
human (signal two 0.20). It worked as an evasion, same as the EV family. PI01, PI03 and PI06 got "unsure", and PI04 (hostile label) can't
work because the label text is a constant in `scoring.py`. PI05 (log injection)
held: `audit.py` uses `json.dumps`, so the quote characters were escaped, and the
log has no unparseable line.

*MF07 (Arabic sentence) got `ai`, 0.8157, a high-confidence accusation (stage:
all three).* The route's length check uses `text.split()`, so any text with five
space-separated tokens passes. Signal two's `words()` only matches a-z and
digits, so it sees zero words: no vocabulary (variety scores as maximally
repetitive) and no punctuation (scores maximally machine-like), giving 0.725.
Signal one is gpt2, an English model. It splits the Arabic text into about
one token per character (103 tokens for 105 characters, only 41 distinct), and
scores it at perplexity 10.9, which is very predictable (0.91). Neither signal
is defined for non-Latin script, and nothing checks.

*MF04 (punctuation only) got a decision (stage: the route).* `!!! ??? ... ,,,
;;; --- ((( )))` is eight tokens by `text.split()`, so it passed the minimum
length check and was scored (0.465, unsure). Not a crash, but a label on
something that isn't writing.

*RQ10 and RQ11 got 429 instead of 400 (stage: the rate limiter, not my route).*
The limiter runs before the route and counts refused requests. The address-wide
bucket had been used up by earlier malformed rows that had no usable
`creator_id`, so these two never reached my validation. Held, but one address
sending bad requests can lock itself out of `/submit`.

*The pattern.* Three problems account for nearly everything. (1) Signal two
treats plain, even, unpunctuated writing as machine-like, and signal one
partly agrees: criterion 1, FP02, FP03, and by extension FP05. (2) Any edit that
moves just one signal turns a split into "unsure", so no evasion needs to fool
both: the ten EV rows and PI02. (3) The route's input check counts tokens, not
words: MF04 and MF07.

---

## The Improvement

**What I changed:** One number, `AI_THRESHOLD` in `config.py`, from 0.65 to
0.72. That is the only change in the unit besides the rate limiter and the log.
The unsure band went from 0.35 to 0.65 (0.30 wide) to 0.35 to 0.72 (0.37 wide).
The label text didn't change, and neither did either signal, the weights, or the
combining rule.

**Which diagnosis pointed at it:** The criterion 1 miss. The two plain pieces
that got called AI scored 0.698 and 0.7065, and the highest human piece after
them was 0.61. I put the line just above the highest human piece. I did not
pick the signal two fix (its punctuation and sentence-spread parts treat plain
writing as machine-like) because that is several changes tuned at once, and I
couldn't have told them apart afterwards. I also did not pick the route
validation fix for MF04 and MF07, though it's the other obvious candidate; see
What's Still Broken.

### Attack Run — After

Same 56 attacks, same command with `--label after`, same verdict rule as
before. Full output: `results/attack_run_2026-11-10_0515_after.md`.

**Result: 14 broke, 42 held, no crashes.** Before it was 16 broke, 40 held.

| Family | Broke before | Broke after |
|---|---|---|
| evasion | 10 | 10 |
| false_positive | 3 | 1 |
| prompt_injection | 1 | 1 |
| malformed | 2 | 2 |
| flood_same_creator | 0 | 0 |

I diffed every row of the two runs. Exactly two of the 56 changed, FP02 and
FP03, both from `ai` to `unsure`, with identical scores (0.6921 and 0.6996).
Nothing else moved, which is what a one-number change should look like.

| ID | Family | What it was going for | Status | Label | Score | Verdict |
|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | unsure | 0.450 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.460 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.480 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | unsure | 0.617 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.265 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.456 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.479 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | unsure | 0.455 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.512 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | unsure | 0.634 | BROKE |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | unsure | 0.527 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | unsure | 0.692 | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | unsure | 0.700 | HELD |
| FP04 | false_positive | a student essay written to a rubric | 200 | unsure | 0.584 | HELD |
| FP05 | false_positive | technical documentation written by a person | 200 | ai | 0.743 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.571 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | unsure | 0.566 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | unsure | 0.388 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | unsure | 0.389 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.200 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.506 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | unsure | 0.449 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | unsure | 0.494 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | unsure | 0.505 | HELD |
| MF01 | malformed | text is only whitespace | 400 | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | — | — | HELD |
| MF03 | malformed | text is control characters | 400 | — | — | HELD |
| MF04 | malformed | text is only punctuation | 200 | unsure | 0.465 | BROKE |
| MF05 | malformed | text is a very long single word | 400 | — | — | HELD |
| MF06 | malformed | text is emoji only | 400 | — | — | HELD |
| MF07 | malformed | text is right-to-left script | 200 | ai | 0.816 | BROKE |
| MF08 | malformed | text is 60,000 characters | 413 | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | — | — | HELD |
| RQ05 | malformed | text is null | 400 | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.401 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | HELD |

**The five criteria, three trials each, after** (`results/run_2026-11-10_0515_after.md`).
All three trials were identical again.

| Criterion | Target | Before (3 trials) | After (3 trials) | Verdict before | Verdict after |
|---|---|---|---|---|---|
| 1. Own writing rarely called AI | 1 of 10 at most, none above 0.80, 4+ plain | 2/10, 2/10, 2/10 | 0/10, 0/10, 0/10 (top 0.71) | MISSED | MET |
| 2. Clearly AI and clearly human score apart | gap 0.30+, lowest AI above highest human | gap 0.43 x3 | gap 0.43 x3 | MET | MET |
| 3. All three labels reachable | 3 of 3, unsure band 0.25+, 0.51 and 0.95 differ | 3/3, band 0.30 | 3/3, band 0.37 | MET | MET |
| 4. Appeal changes status and is recorded | 10 of 10, refused appeals write nothing | 10/10, 2 log lines written | 10/10, 2 log lines written | MISSED | MISSED |
| 5. Bad input refused cleanly | 6 of 6, none 500, all logged, ping ok | 6/6 x3 | 6/6 x3 | MET | MET |

**Did it help, and how do I know:** Yes, on the thing it was aimed at, and the
evidence is the two tables above: criterion 1 went from 2 of 10 flagged to 0 of
10 in every trial, and FP02 and FP03 stopped being called AI. It did nothing
for the other 14 broken attacks, and it was never going to, since none of them
was a score sitting between 0.65 and 0.72.

It cost something, and I want to be straight about it.

- **Less AI text gets the AI label.** Of my five clean AI paragraphs, 3 were
  labeled AI at 0.65 (0.7326, 0.7708, 0.6998) and 2 are at 0.72. The one that
  dropped out is the 0.6998 one. That's a real loss of detection, and the attack
  set can't show it, because none of its AI-written rows (evasion and injection)
  got the AI label either before or after.
- **The criterion 1 pass is not independent evidence.** I chose 0.72 after
  looking at the scores of these same ten stand-in pieces, so passing them is
  close to guaranteed. It shows the threshold does what I meant it to do. It
  doesn't show that a stranger's plain writing would stay under it. FP05
  (technical documentation, 0.7432) is a human piece that is still over 0.72,
  and it's the honest counterexample.
- **It trades off, and doesn't fix.** Plain human text and clean AI text overlap
  (0.60 to 0.78 against up to 0.71). Moving the line only chooses which side of
  the overlap gets hurt. I chose to protect the writer.

---

## What's Still Broken

**What's still broken, and what I'd do about it:**

- **All 10 evasion attacks still get no AI label** (EV05 gets "human"). Each one
  moves only one signal, and the combining rule turns a split into "unsure". I'd
  need a signal that doesn't move when someone adds typos or breaks up
  sentences, something that looks at content rather than shape, and I'd want
  far more than five AI samples to place the line. I stopped because one change
  was allowed, and because lowering the AI line to catch them (the only quick
  option) would undo criterion 1, since they overlap with plain human text.
- **PI02** (a fake "SYSTEM:" header) gets "human", 0.20, the same mechanism as
  the evasion rows: it works by making the text look odd to both signals. It
  isn't really an injection, nothing reads it as instructions. Same fix, same
  reason I stopped.
- **FP05** (technical documentation by a person, 0.7432) is still labeled AI.
  Both signals agree, so no combining rule helps. A signal that doesn't punish a
  plain technical register is what it needs. Raising the line again to 0.75 would
  clear it, but I'd be fitting to the attack set, and every step up leaves more
  AI text unflagged.
- **MF07** (an Arabic sentence) gets `ai` at 0.8157, which is the worst thing
  left: a high-confidence accusation on text neither signal can read. The fix is
  small and I think clearly right: count real words with `stylometry.words()`
  instead of `text.split()` in the route, and refuse text with too few. That also
  fixes **MF04** (punctuation only). I didn't do it because it would have been a
  second change in the same before/after, and I'd put it first next time.
- **Criterion 4 is still missed** by the two `rejected` lines a refused appeal
  writes. I could stop logging refused appeals, but then a flood of bad appeals
  would be invisible, which is the exact thing Milestone 1 told me to avoid. I'd
  keep logging and rewrite the criterion so it says "writes no appeal entry".
  The rules say a criterion that measures fine and was missed can't be
  revised, so it stays missed in this unit.
- **RQ10 and RQ11** get a 429 instead of a 400, because the limiter counts
  refused requests and the shared address bucket fills up. I'd exempt requests
  that fail validation from the count. I stopped because it's an edge case and
  nothing crashed.
- **Criterion 1 needs real writing.** Its verdict is for ten stand-in pieces
  written by the AI assistant. I'd re-run it on ten real pieces before trusting
  either the miss or the pass.

**The trade I'd make if this ran for real:**

I'd keep the unsure band wide and protect the writer: a wrong accusation lands on
one person with no easy way to argue, while a missed AI paragraph costs the site
a little. The people who pay are the readers and moderators who then see more AI
text with no flag on it, and, since the evidence says plain and second-language
writing is what gets accused, I'd rather that cost land on them than on those
writers.

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


---

# Capstone — Deploy and instrument Provenance Guard

Everything above is the system as it stood after unit 8. Everything below this
line is the capstone, in the order the brief asks for it.

## What This Extends

**Provenance Guard** (project 4, the AI-text detector service). It already had
`POST /submit`, `POST /appeal`, two signals, three labels, rate limiting and a
decision audit log (`logs/audit.jsonl`).

**What's new:** an operational layer around it.

- a per-request telemetry record (`logs/requests.jsonl`, written by
  `telemetry.py`) with the input, output, outcome and timings of *every*
  `/submit` call, including rejections, rate limits and crashes;
- a documented single-command run path with a clean-checkout test
  (`RUNNING.md`);
- a measured cost per run, in seconds of compute;
- a capstone test harness (`run_capstone.py`) that runs the five new criteria
  three times each.

## The Shape

**Shape A — Deploy and instrument.** The service already worked on my laptop and
only ever ran from my editor. This unit I put a run path and a measuring layer
around it and then tested the numbers that come out of it. The model, the two
signals, the thresholds and the labels are not touched.

**Run path: B (local, with logs).** `RUNNING.md` has the command. The reason is
arithmetic, not preference: gpt2 is ~550 MB on disk and torch is another few
hundred MB in RAM, against a 512 MB free host.

**Out of scope — decided before building, on purpose:**

- *No new detection signal and no re-tuning of weights or thresholds.* That is a
  different project, and the labels were already tested in unit 8.
- *No hosted deployment, no Docker, no gunicorn.* gunicorn does not run on
  Windows, and the host is the wrong size for the model anyway.
- *No change to the decision audit log's shape.* `logs/audit.jsonl` keeps its
  nine fields so unit 8's entries stay comparable with new ones. Telemetry is a
  separate file.
- *No load test beyond one local client.* (Listed as a stretch; not claimed.)

Size check: the telemetry layer is one new module plus two hooks in `app.py`.
That is one piece of work, not three.


## Running It

**Path B — local, with logs.** Start command, environment and the reasoning for
not hosting are in [RUNNING.md](RUNNING.md) (top section). Short version:

```bash
AI201_DEBUG=0 .venv/Scripts/python app.py
```

**Tested from a clean clone.** I cloned the repo (branch `capstone`, since merged into `main`) into a new folder
and followed RUNNING.md. It worked, and the test turned up two things a reader
would have hit:

1. **I reused my existing virtual environment** (Python 3.12.10 with torch
   already installed) instead of reinstalling torch, to save a ~200 MB download
   and a long install. So the `pip install` step in RUNNING.md was *not*
   re-executed from zero this unit; it is the unchanged unit 7 requirements
   file. The model was also already in my Hugging Face cache. A first-time
   reader pays the 550 MB download.
2. The first draft of RUNNING.md forgot that port 5000 may already be taken (it
   was: another process of mine was running the unit 8 service). `PORT` is now
   named in the file.

In the clone, `GET /health` answered, one `/submit` returned 200 and wrote a
record to `logs/requests.jsonl`, and `python test.py` passed 9 of 9.

## Instrumentation

**Two logs, two jobs.**

- `logs/audit.jsonl` (unchanged, `audit.py`) — one record per *decision* and per
  appeal, nine fixed fields. It is what `/appeal` reads.
- `logs/requests.jsonl` (new, `telemetry.py`) — one record per `/submit` *call*,
  whatever its fate. Written by Flask `before_request`/`after_request` hooks in
  `app.py`, so the handler cannot skip it. The hooks are registered before the
  rate limiter, because the limiter aborts the request chain with a 429 and a
  hook registered after it would never start its timer.

Fields in a `requests.jsonl` record:

| Field | What it holds |
|---|---|
| `timestamp`, `request_id` | UTC time; 12-hex id, also sent back as `X-Request-Id` |
| `route`, `creator_id` | what was called, and who it counted against |
| `text_type`, `text_chars`, `text_hash` | the input: its type, length, and a 12-hex hash (never the text) |
| `status_code`, `outcome`, `reason` | the output: HTTP code; `decided` / `rejected` / `rate_limited` / `error`; the error code |
| `content_id`, `guess`, `confidence`, `model_score`, `style_score` | the decision, when there was one |
| `duration_ms`, `cpu_ms` | wall-clock and process CPU time over the request |
| `detector_cold` | true if the gpt2 model had to be loaded during this request |

Fourteen real records, pasted as text from `logs/requests.jsonl`. The first is
the cold first request after a fresh start, then one warm one, then a mixed
session: a normal submission, missing text, empty text, a 25,000-character text
(413), a null text, five more submissions from one creator (the last two came back
429).

```json
{"timestamp": "2026-11-10T09:07:18+00:00", "request_id": "04c1bead40dd", "route": "/submit", "creator_id": "cost_0", "text_type": "str", "text_chars": 411, "text_hash": "e570ed33b3c2", "status_code": 200, "outcome": "decided", "reason": null, "content_id": "08aeed665a55", "guess": "unsure", "confidence": 0.5701, "model_score": 0.848, "style_score": 0.4325, "duration_ms": 3532.6, "cpu_ms": 6984.4, "detector_cold": true}
{"timestamp": "2026-11-10T09:07:19+00:00", "request_id": "6cd98123a6ee", "route": "/submit", "creator_id": "cost_1", "text_type": "str", "text_chars": 411, "text_hash": "e570ed33b3c2", "status_code": 200, "outcome": "decided", "reason": null, "content_id": "00cb5ee65fdd", "guess": "unsure", "confidence": 0.5701, "model_score": 0.848, "style_score": 0.4325, "duration_ms": 88.3, "cpu_ms": 1375.0, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "e956ee22da1a", "route": "/submit", "creator_id": "demo_a", "text_type": "str", "text_chars": 104, "text_hash": "9ec2eb81af18", "status_code": 200, "outcome": "decided", "reason": null, "content_id": "a98e69ca189a", "guess": "unsure", "confidence": 0.6212, "model_score": 0.6794, "style_score": 0.563, "duration_ms": 3514.9, "cpu_ms": 10171.9, "detector_cold": true}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "347c2b1b6797", "route": "/submit", "creator_id": "demo_b", "text_type": "NoneType", "text_chars": null, "text_hash": null, "status_code": 400, "outcome": "rejected", "reason": "bad_text", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 0.7, "cpu_ms": 0.0, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "3d6568f6efc7", "route": "/submit", "creator_id": "demo_c", "text_type": "str", "text_chars": 0, "text_hash": "e3b0c44298fc", "status_code": 400, "outcome": "rejected", "reason": "text_too_short", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 0.7, "cpu_ms": 0.0, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "8d7abfd28fa8", "route": "/submit", "creator_id": "demo_d", "text_type": "str", "text_chars": 25000, "text_hash": "022625a9ba7a", "status_code": 413, "outcome": "rejected", "reason": "text_too_long", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 0.5, "cpu_ms": 0.0, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "d97ebbe2cef5", "route": "/submit", "creator_id": "demo_e", "text_type": "NoneType", "text_chars": null, "text_hash": null, "status_code": 400, "outcome": "rejected", "reason": "bad_text", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 0.4, "cpu_ms": 0.0, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "9d8c1080b224", "route": "/submit", "creator_id": "demo_flood", "text_type": "str", "text_chars": 104, "text_hash": "9ec2eb81af18", "status_code": 200, "outcome": "decided", "reason": null, "content_id": "ef60ad600118", "guess": "unsure", "confidence": 0.6212, "model_score": 0.6794, "style_score": 0.563, "duration_ms": 38.2, "cpu_ms": 671.9, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "c4ede4b335bb", "route": "/submit", "creator_id": "demo_flood", "text_type": "str", "text_chars": 104, "text_hash": "9ec2eb81af18", "status_code": 200, "outcome": "decided", "reason": null, "content_id": "34e84a19e9f7", "guess": "unsure", "confidence": 0.6212, "model_score": 0.6794, "style_score": 0.563, "duration_ms": 40.1, "cpu_ms": 843.8, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "b6d62bf9aace", "route": "/submit", "creator_id": "demo_flood", "text_type": "str", "text_chars": 104, "text_hash": "9ec2eb81af18", "status_code": 200, "outcome": "decided", "reason": null, "content_id": "07265b4edba6", "guess": "unsure", "confidence": 0.6212, "model_score": 0.6794, "style_score": 0.563, "duration_ms": 65.5, "cpu_ms": 1156.2, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "97ffce2eab5b", "route": "/submit", "creator_id": "demo_flood", "text_type": "str", "text_chars": 104, "text_hash": "9ec2eb81af18", "status_code": 200, "outcome": "decided", "reason": null, "content_id": "0c1d7e72f6f4", "guess": "unsure", "confidence": 0.6212, "model_score": 0.6794, "style_score": 0.563, "duration_ms": 53.7, "cpu_ms": 1046.9, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "9692bcaeae4e", "route": "/submit", "creator_id": "demo_flood", "text_type": "str", "text_chars": 104, "text_hash": "9ec2eb81af18", "status_code": 200, "outcome": "decided", "reason": null, "content_id": "7742b9a8bd4a", "guess": "unsure", "confidence": 0.6212, "model_score": 0.6794, "style_score": 0.563, "duration_ms": 48.8, "cpu_ms": 875.0, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "0a9c803c19fc", "route": "/submit", "creator_id": "demo_flood", "text_type": "str", "text_chars": 104, "text_hash": "9ec2eb81af18", "status_code": 429, "outcome": "rate_limited", "reason": "rate_limited", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 0.8, "cpu_ms": 0.0, "detector_cold": false}
{"timestamp": "2026-11-10T09:08:11+00:00", "request_id": "e657fc271feb", "route": "/submit", "creator_id": "demo_flood", "text_type": "str", "text_chars": 104, "text_hash": "9ec2eb81af18", "status_code": 429, "outcome": "rate_limited", "reason": "rate_limited", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 0.5, "cpu_ms": 187.5, "detector_cold": false}
```

## What It Costs

**One `/submit` costs $0.00 in API spend and, once the model is loaded, about
0.09 seconds of wall-clock and about 1.4 seconds of CPU time** for a ~100-word
text. A cold first request (model not yet loaded) costs about 3.5 s wall and 7 s
CPU, a one-off per service start.

**How I measured it.** `measure_cost.py` starts the service fresh with
`python app.py`, sends one cold request and then ten warm ones (a different
`creator_id` each, so the rate limiter never interferes), and reads
`duration_ms` and `cpu_ms` back out of `logs/requests.jsonl`. These are the
service's own telemetry, not a pricing page.

```
cold request : 3533 ms wall, 6984 ms cpu
warm requests: n=10  mean 86 ms wall, 1447 ms cpu  (min 78, max 92)
API spend per run: $0.00 (no hosted service is called)
```

`cpu_ms` is larger than wall-clock because PyTorch spreads one scoring pass over
several CPU threads; it is process CPU time, not elapsed time. The capstone run
gives a second reading for longer text: mean wall time was 0.09 s at 100 words,
0.18 s at 250 words and 0.24 s at 600 words (cut to 400 tokens). One caveat:
another process of mine (the unit 8 service) was running on the same laptop
during these runs, so wall times may be a little inflated.

**A hundred people a day.** Assume each of 100 people submits 5 drafts a day:
100 x 5 = 500 submissions. At the 250-word mean of 0.18 s wall and the 1.45 s CPU
measured above:

- wall-clock: 500 x 0.18 s = **90 s** of scoring a day;
- CPU: 500 x 1.45 s = **about 725 CPU-seconds** a day, roughly 12 minutes;
- API spend: 500 x $0.00 = **$0.00**.

So the per-request cost is trivial. The real cost of this system is the standing
one: a process holding about 1 GB of RAM for the model, all day, which is exactly
why it does not fit a free 512 MB host.

## Run Log and Verdicts — Capstone

Five criteria from `criteria.md`, three trials each, **before** the fix. Produced
by `run_capstone.py::main`; the full output is in `results/capstone_before.md`
and every service record from the trials is in `logs/capstone_before/`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every /submit call leaves a complete record | 20 of 20, every trial | ✓ 20/20 complete | ✓ 20/20 complete | ✓ 20/20 complete | MET |
| 2. First request after restart ≤ 3.0 s | 3 of 3 starts, every trial | ✗ 0/3 (worst 3.5s) | ✗ 0/3 (worst 3.5s) | ✗ 0/3 (worst 3.7s) | MISSED |
| 3. Warm p95 ≤ 0.5 s, none > 1.5 s | p95 ≤ 0.5 s, every trial | ✓ p95 0.24s, max 0.26s | ✓ p95 0.26s, max 0.27s | ✓ p95 0.36s, max 0.48s | MET |
| 4. Model unavailable → clean 503, logged, service stays up | 5 of 5, every trial | ✓ 5/5 (ping 200, health 200) | ✓ 5/5 (ping 200, health 200) | ✓ 5/5 (ping 200, health 200) | MET |
| 5. Odd but valid text never crashes | 6 of 6, every trial | ✓ 6/6 | ✓ 6/6 | ✓ 6/6 | MET |

**Verdicts: criteria 1, 3, 4 and 5 MET; criterion 2 MISSED.** No criterion was
revised.

Real output from trial 1, one block per criterion (function named at the top of
each).

**Criterion 1** — `run_capstone.py::crit1`, reading
`logs/capstone_before/trial1_c1/requests.jsonl`:

```
{
 "n_records": 20,
 "problems": [],
 "client_statuses": [
  "valid:200",
  "valid:200",
  "valid:200",
  "valid:200",
  "valid:200",
  "valid:200",
  "valid:200",
  "valid:200",
  "no text:400",
  "empty text:400",
  "null text:400",
  "numeric text:400",
  "too long:413",
  "json list:400",
  "flood 1:200",
  "flood 2:200",
  "flood 3:200",
  "flood 4:200",
  "flood 5:200",
  "flood 6:429"
 ]
}
{"timestamp": "2026-11-10T09:10:02+00:00", "request_id": "cb8262d209bf", "route": "/submit", "creator_id": "c1_bad_1", "text_type": "NoneType", "text_chars": null, "text_hash": null, "status_code": 400, "outcome": "rejected", "reason": "bad_text", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 1.0, "cpu_ms": 0.0, "detector_cold": false}
{"timestamp": "2026-11-10T09:10:02+00:00", "request_id": "57994a820fbe", "route": "/submit", "creator_id": "c1_bad_2", "text_type": "str", "text_chars": 0, "text_hash": "e3b0c44298fc", "status_code": 400, "outcome": "rejected", "reason": "text_too_short", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 0.7, "cpu_ms": 0.0, "detector_cold": false}
```

**Criterion 2** — `run_capstone.py::crit2`:

```
{
 "starts": [
  {
   "start": 1,
   "ready_s": 0.51,
   "first_submit_s": 3.39,
   "status": 200
  },
  {
   "start": 2,
   "ready_s": 0.51,
   "first_submit_s": 3.43,
   "status": 200
  },
  {
   "start": 3,
   "ready_s": 0.51,
   "first_submit_s": 3.53,
   "status": 200
  }
 ]
}
```

**Criterion 3** — `run_capstone.py::crit3`:

```
{
 "p95_s": 0.245,
 "max_s": 0.265,
 "median_s": 0.168,
 "mean_s_by_words": {
  "100": 0.094,
  "250": 0.179,
  "600": 0.24
 },
 "all_200": true
}
```

**Criterion 4** — `run_capstone.py::crit4`, model name `no-such-model-capstone`:

```
{
 "statuses": [
  503,
  503,
  503,
  503,
  503
 ],
 "ms": [
  2687,
  3,
  13,
  12,
  13
 ],
 "bodies": [
  {
   "error": "detector_unavailable",
   "message": "The model isn't available right now."
  },
  {
   "error": "detector_unavailable",
   "message": "The model isn't available right now."
  }
 ]
}
{"timestamp": "2026-11-10T09:10:27+00:00", "request_id": "5225c341ea60", "route": "/submit", "creator_id": "c4_0", "text_type": "str", "text_chars": 292, "text_hash": "cc09c9587a5f", "status_code": 503, "outcome": "error", "reason": "detector_unavailable", "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "duration_ms": 2672.5, "cpu_ms": 2625.0, "detector_cold": true}
```

**Criterion 5** — `run_capstone.py::crit5`:

```
no punctuation       status 200  0.11s  model/style/conf = [0.3753, 0.6293, 0.5023]
one 3000-char word   status 200  0.2s  model/style/conf = [0.997, 0.575, 0.643]
60 emoji             status 200  0.08s  model/style/conf = [0.9971, 0.725, 0.861]
arabic paragraph     status 200  0.09s  model/style/conf = [0.991, 0.725, 0.858]
word x200            status 200  0.15s  model/style/conf = [0.997, 0.725, 0.861]
newlines and tabs    status 200  0.13s  model/style/conf = [0.0, 0.725, 0.4313]
```

### Diagnosis — criterion 2 (the only miss)

All nine fresh starts in three trials missed, by the same margin: the first
`/submit` took 3.39 to 3.73 s against a 3.0 s target, while `/health` answered
after 0.51 s. The telemetry record of a cold request says why: it has
`detector_cold: true`, `duration_ms: 3386` and `cpu_ms: 5781`, against about 90 ms
for the same text once warm.

- **Stage:** the detector, `detector.py::_load`.
- **Mechanism:** the model is loaded lazily, inside the first request that needs
  it (`perplexity()` calls `_load()`). So the service reports itself healthy half
  a second after launch while the part that does the work has not been loaded,
  and whichever writer arrives first pays the ~3.3 s load. It is one problem seen
  nine times, not nine problems.

The other four criteria met their targets in all three trials. The narrowest
margin was criterion 3, trial 3: p95 0.36 s against 0.5 s.

**One thing the numbers hide.** Criterion 5 only asked that odd text not crash
the service, and it didn't. But look at the scores above: 60 emoji, an Arabic
paragraph and "hello" x200 all come back with a confidence of about 0.86, which
is the high-confidence-AI band. A real person writing in Arabic would be told
their work looks machine-made. That is the unit 7 blind spot (the model signal
rewards predictability, and gpt2 is an English model) showing up where my
capstone criteria set no target. I am reporting it rather than quietly passing
criterion 5.

## The Improvement — Capstone

**One change:** `app.py::main` now calls `detector.warm_up()` before it starts
serving, so the model is loaded before the first request can arrive. If the load
fails the service still starts and `/submit` answers 503 per request, as before
(criterion 4 covers that, and still passes).

**Why:** it follows the diagnosis directly. The cost of the first request was the
model load, so the load moves to start-up.

**Prediction, written in the commit message before the re-run:** criterion 2
met; time-to-ready rises from about 0.5 s to about 4 s; nothing else moves.

Both result sets side by side (`results/capstone_before.md`, above, and
`results/capstone_after.md`, below):

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every /submit call leaves a complete record | 20 of 20, every trial | ✓ 20/20 complete | ✓ 20/20 complete | ✓ 20/20 complete | MET |
| 2. First request after restart ≤ 3.0 s | 3 of 3 starts, every trial | ✓ 3/3 (worst 0.3s) | ✓ 3/3 (worst 0.3s) | ✓ 3/3 (worst 0.3s) | MET |
| 3. Warm p95 ≤ 0.5 s, none > 1.5 s | p95 ≤ 0.5 s, every trial | ✓ p95 0.25s, max 0.28s | ✓ p95 0.28s, max 0.30s | ✓ p95 0.28s, max 0.30s | MET |
| 4. Model unavailable → clean 503, logged, service stays up | 5 of 5, every trial | ✓ 5/5 (ping 200, health 200) | ✓ 5/5 (ping 200, health 200) | ✓ 5/5 (ping 200, health 200) | MET |
| 5. Odd but valid text never crashes | 6 of 6, every trial | ✓ 6/6 | ✓ 6/6 | ✓ 6/6 | MET |

| | Before | After |
|---|---|---|
| Time until `/health` answers (9 starts) | 0.51-0.52 s | 3.71-3.72 s |
| First `/submit` after `/health` (9 starts) | 3.39-3.73 s | 0.25-0.32 s |
| Warm p95 (criterion 3, 3 trials) | 0.25 / 0.26 / 0.36 s | 0.25 / 0.28 / 0.28 s |
| Criteria met | 4 of 5 | 5 of 5 |

**Did it help?** Yes, for what it targeted: criterion 2 went from 0 of 9 starts
to 9 of 9, and nothing else moved (criterion 3's differences sit inside the
run-to-run spread already visible within the "before" trials).

**The trade, named.** The wait did not disappear, it moved: the service now takes
about 3.7 s to start answering `/health` instead of 0.5 s. That is the right place
for it, since nobody is waiting on it, but a supervisor that restarts the service
and checks `/health` straight away now has to wait longer. The first request is
also still about 3x slower than a warm one (0.25-0.32 s vs 0.09 s); that is
first-inference setup in PyTorch, which loading the weights does not remove. And
this helps only when the service is started with `python app.py`: a server that
imports `app` without running `main()` (gunicorn on Linux) would skip the warm-up
and need it moved to import time.

Regression check: `python test.py` passes 9 of 9, and criteria 1, 4 and 5 (which
exercise `/submit`, rejections and the failure path) still pass after the change.

## What's Still Broken — Capstone

No criterion is missed after the fix, but my own tests leave real gaps:

1. **Non-English and degenerate text gets a confident "AI" label** (see above).
   This is the false-accusation risk the whole project is about, and my five
   criteria never set a number for it. *What I'd do:* add a criterion for
   non-Latin-script and very repetitive text ("at most 1 of 6 may be labelled
   high-confidence AI") and make the likely fix a gate that returns `unsure` when
   the text is mostly outside the Latin script or has very few distinct words.
   *Why I stopped:* it changes labelling behaviour, which this unit scoped out on
   purpose.
2. **Single client only.** Every number is one client, one request at a time, on
   the Flask server. I did not test concurrency; one process with torch will
   serialise requests. Not attempted (a stretch item, not claimed).
3. **Limiter state is in memory.** A restart forgets every count, and a creator
   can dodge the limit by changing `creator_id`.
4. **Hosted path not attempted.** Path B only, by the arithmetic in RUNNING.md.
5. **The clean-checkout test reused my existing virtualenv** and model cache, so
   a first-time install on a bare machine is untested.
6. **The logged `duration_ms` was not independently checked** against a client
   stopwatch. The cost and latency numbers lean on it. The client-side timings in
   `run_capstone.py` agree in rough size (about 0.09 s warm in both), but I wrote
   no criterion for it.

**The one thing I'd do first:** item 1. It is the only gap where the system hurts
a person rather than just being slow, and it is the one my own criteria let
through.

**If this were real and I had another unit:** I'd write the criterion for item 1
first and run it three times before touching any code, then decide between a
script gate and a calibration change. I'd do that before anything operational,
because a faster, better-logged service that accuses the wrong writers faster is
not an improvement.

## How I Used AI

I used Claude Code (Sonnet 5.5) throughout this capstone, with the aim of
keeping hardware, compute and input low. It built the telemetry layer and test
harness and ran the trials. Two specific moments:

1. **Another session was writing in the same repo.** While starting the build,
   Claude noticed new lines appearing in `logs/audit.jsonl` and a Python server
   running that it had not started: a second Claude session was running unit 8
   attack tests in this repository at the same time. Claude checked the session
   list, moved its uncommitted edits into a separate git worktree on a `capstone`
   branch, restored the shared checkout, and pointed every test run at its own
   log directory (`AI201_LOG_DIR`) so trials could not mix into the other
   session's log. What changed: I did the work on branch `capstone` and merged it into `main` afterwards.
2. **Telemetry hook order.** I asked for a per-request log that could not miss a
   rejected request. Claude reasoned that Flask stops running `before_request`
   hooks at the first one that raises, and the rate limiter raises a 429, so a
   hook registered after the limiter would never start its timer for exactly the
   requests I most want a record of. It registered the hooks first, then checked
   it by sending six requests from one creator, which produced a 429 record with a
   real duration. Separately, the docs say the first request takes 10-20 s; the
   smoke test showed 3.7 s, so the cold-start target (3.0 s) was set from what a
   user will tolerate, and both facts are stated at the top of `criteria.md`.
