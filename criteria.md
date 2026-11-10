# Capstone acceptance criteria — Provenance Guard, operational layer

Written **before any trial was run**. (The unit 7 criteria, about the detector
itself, are kept in `criteria_unit7.md`.)

Shape A: the extension is the run path, the per-request log and the numbers that
come out of it. Criteria **1–4 are about the extension**. Criterion 5 is about
the system as it already worked.

Two honest notes on what I knew when I wrote these. I had already seen, while
checking the build, one cold first request of about 3.7 s and warm requests of
under 100 ms for a ~100-word text, on my laptop. The cold-start and latency
targets below are set from what a user would put up with, not from those
numbers. One trial = everything below run once, from fresh service processes. A
criterion is **met only if every one of the three trials meets its target.**

---

## 1. Every call to /submit leaves a complete record

I send 20 requests to one fresh service, in this mix: 8 valid submissions (a
different `creator_id` each), 4 invalid ones (no `text`, empty `text`, `text` as
`null`, `text` as a number), 1 `text` over the length limit, 1 body that is a
JSON list instead of an object, and 6 from a single `creator_id` (the first 5
are allowed, the 6th must be rate-limited).

**Target:** exactly 20 new lines appear in `logs/requests.jsonl` — one per
request, no more, no fewer — and every one of them has all 18 fields from
`telemetry.py` present, a `status_code` equal to the status the client actually
received, and a non-null `duration_ms`. 20 of 20 in all three trials.

**Why this target:** the failure I am guarding against is the one that shows up
only as an absence. A rejected or rate-limited request that leaves no record
looks identical to a quiet afternoon, so the number has to be exact, not "most".
`status_code` must match what the client saw because a log that disagrees with
reality is worse than none.

---

## 2. The first request after a restart is not painful

I start a fresh service process, wait until `/health` answers, then send one
valid ~100-word submission and time it from the client. Three fresh starts per
trial.

**Target:** the first `/submit` returns 200 in **3.0 seconds or less**, on all 3
starts of every trial.

**Why this target:** the model loads lazily on the first request, and the starter
docs warn that this takes 10–20 s. A writer who submits a draft right after a
restart and stares at a spinner for 15 s will assume it is broken. 3 s is about
where waiting stops feeling like a delay and starts feeling like a fault. I did
not pick 5 s, because at 5 s I would be excusing the very cost this criterion
exists to catch.

---

## 3. A warm submission comes back quickly

On a service that has already loaded the model, I send 20 valid submissions one
after another (a different `creator_id` each): 8 of about 100 words, 6 of about
250 words, 6 of about 600 words (the detector reads only the first 400 tokens,
so the longest are cut). I time each from the client.

**Target:** the 95th-percentile time (the 19th-fastest of 20) is **0.5 seconds or
less**, and none takes over 1.5 seconds. Every trial.

**Why this target:** a writer sends a draft and reads the label, so under half a
second feels instant. Rate limiting already caps a creator at 5 a minute, so
nobody needs more throughput than this. I included the long texts on purpose:
the cost of scoring grows with length up to the 400-token cap, and the short
text alone would flatter the number.

---

## 4. If the model cannot load, the service says so and stays up

I start a service whose detector model cannot be loaded (`AI201_DETECTOR_MODEL`
set to a name that does not exist, with `HF_HUB_OFFLINE=1`) and send 5 valid
submissions, each from a different `creator_id`.

**Target:** all 5 get HTTP 503 with a JSON body whose `error` is
`detector_unavailable`, each within 5 seconds; none gets a 500 or hangs; all 5
leave a `requests.jsonl` record with `outcome` = `error` and `reason` =
`detector_unavailable`; and `/ping` and `/health` still answer 200 afterwards.
5 of 5, every trial.

**Why this target:** this is the realistic bad path for this service — a missing
or corrupt model download, or a disk that filled up. The wrong behaviours are a
crash (the whole service dies and `/appeal` goes with it) or a silent success
with a made-up score, which would accuse or clear a real writer on no evidence.
It is 5 of 5 because the handler has one branch for it and there is no excuse
for it to be flaky.

---

## 5. Odd but valid text does not crash the service

(About the system as it already worked, not the extension.) I send 6 inputs that
are legal under the length rules but nothing like normal prose: 100 words with no
punctuation at all; 4 short words plus one 3,000-character word with no spaces;
60 emoji separated by spaces; a paragraph in Arabic script; the same word
repeated 200 times; and text broken up with many newlines and tabs.

**Target:** all 6 return 200 with `model_score`, `style_score` and `confidence` as
numbers between 0 and 1, within 5 seconds each; none returns 500. 6 of 6, every
trial.

**Why this target:** unit 8's bad-input criterion only covered *invalid*
requests. People paste odd things — a poem, a transcript, a line of emoji, text
in another script — and a divide-by-zero in the style signal would turn that into
a 500 and an unexplained failure for someone who did nothing wrong. 6 of 6
because any crash is a real bug, not a rate.
