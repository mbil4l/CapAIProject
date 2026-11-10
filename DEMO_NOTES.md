# Demo notes (unit 10) — Provenance Guard capstone

Three minutes, four beats. Numbers are from `results/capstone_before.md` and
`results/capstone_after.md`.

**1. What I built (45 s).** Provenance Guard is a web service that reads a piece
of writing and says "probably human", "unsure" or "probably AI", using a local
gpt2 model plus a style measure, with an appeal route. The capstone put an
operational layer around it: one log record per request (input, output, outcome,
wall and CPU time), a one-command run path, and a measured cost. Show: start it
with `AI201_DEBUG=0 .venv/Scripts/python app.py`, send one `/submit`, then
`tail -n 1 logs/requests.jsonl`.

**2. What standard I set (30 s).** Read out two criteria with their numbers:
"The first request after a restart returns in 3.0 s or less, on 3 of 3 fresh
starts" and "If the model can't load, 5 of 5 submissions get a clean 503, are
logged, and /ping and /health still answer."

**3. What the test found (60 s).** Criterion 2 missed on all nine starts: the
first request took 3.4-3.7 s because the model loads inside it, while `/health`
said the service was fine after 0.5 s. The other four criteria were met. Also say
the thing the numbers hid: odd text like an Arabic paragraph passed "doesn't
crash" but came back about 0.86 confident AI.

**4. What I changed (45 s).** Load the model at start-up. First request went to
0.25-0.32 s, all five criteria met. The trade: start-up now takes about 3.7 s
before `/health` answers. Still broken: non-English text gets a confident AI
label, nothing tested under concurrent load, and the criteria were drafted by
Claude on my instruction, so I should say that out loud.

**Peer-test heads-up for whoever runs it:** the first run downloads about 550 MB
(`python detector.py`); try empty text, a 25,000-character paste, and a
paragraph in another language.
