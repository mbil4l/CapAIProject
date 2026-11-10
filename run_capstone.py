#!/usr/bin/env python3
"""
Run the five capstone criteria (criteria.md), three trials each.

    python run_capstone.py --label before
    python run_capstone.py --label after

Every trial starts its own service processes with `servectl.py` — the same
`python app.py` RUNNING.md documents — so the cold-start numbers are real cold
starts. Each trial's service writes its logs under `logs/capstone_<label>/`,
which are committed as the run record.

Targets are the ones written in `criteria.md` before any trial was run. This
file only computes whether a trial met them; it does not choose them.

Writes `results/capstone_<label>.md`: the run log table, then real output.
"""

import argparse
import datetime as dt
import json
import statistics
import sys
import time
from pathlib import Path

import requests

import servectl

ROOT = Path(__file__).parent
PORT = 5059
URL = f"http://127.0.0.1:{PORT}"

FIELDS = ["timestamp", "request_id", "route", "creator_id", "text_type",
          "text_chars", "text_hash", "status_code", "outcome", "reason",
          "content_id", "guess", "confidence", "model_score", "style_score",
          "duration_ms", "cpu_ms", "detector_cold"]

# ── Inputs. Plain sentences of my own, recombined for length. ────────────────
_SENTENCES = [
    "I got home late because the bus broke down near the bridge.",
    "My sister called while I was cooking and we talked for an hour.",
    "The report is due on Friday, so I will start on it tomorrow.",
    "We never found the keys, even after we turned the whole house over.",
    "He says the new place is quiet, but the neighbours play music at night.",
    "I think the exam was fair, though the last question took me ages.",
    "There was a long line at the bank, and the machine was out of order.",
    "She planted tomatoes along the fence and they grew taller than me.",
]


def text_of(words: int, seed: int = 0) -> str:
    out, i = [], seed
    while sum(len(s.split()) for s in out) < words:
        out.append(_SENTENCES[i % len(_SENTENCES)])
        i += 1
    return " ".join(" ".join(out).split()[:words])


def submit(body, timeout=60, url=URL):
    t0 = time.perf_counter()
    try:
        r = requests.post(f"{url}/submit", json=body, timeout=timeout)
        ms = (time.perf_counter() - t0) * 1000
        try:
            payload = r.json()
        except ValueError:
            payload = {}
        return {"status": r.status_code, "ms": ms, "json": payload,
                "request_id": r.headers.get("X-Request-Id")}
    except requests.RequestException as exc:
        return {"status": None, "ms": (time.perf_counter() - t0) * 1000,
                "json": {}, "request_id": None, "error": repr(exc)}


def read_records(log_dir: Path):
    path = log_dir / "requests.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


class Service:
    """A fresh service process with its own log directory."""

    def __init__(self, log_dir: Path, extra_env=None):
        self.log_dir = log_dir
        self.proc, self.t_launch = servectl.start(
            PORT, log_dir=log_dir, extra_env=extra_env,
            out_path=log_dir / "server_stdout.txt")

    def ready(self):
        servectl.wait_ready(PORT, self.proc)

    def stop(self):
        servectl.stop(self.proc)
        time.sleep(0.5)


# ── The five criteria. Each returns (cell, met, raw) for one trial. ──────────

def crit1(log_dir: Path):
    svc = Service(log_dir)
    try:
        svc.ready()
        sent = []   # (label, response)
        for i in range(8):
            sent.append(("valid", submit({"text": text_of(60, i), "creator_id": f"c1_ok_{i}"})))
        for label, body in [
            ("no text", {"creator_id": "c1_bad_1"}),
            ("empty text", {"text": "", "creator_id": "c1_bad_2"}),
            ("null text", {"text": None, "creator_id": "c1_bad_3"}),
            ("numeric text", {"text": 12345, "creator_id": "c1_bad_4"}),
            ("too long", {"text": "word " * 5000, "creator_id": "c1_long"}),
            ("json list", [1, 2, 3]),
        ]:
            sent.append((label, submit(body)))
        for i in range(6):
            sent.append((f"flood {i+1}", submit({"text": text_of(60, i), "creator_id": "c1_flood"})))
    finally:
        svc.stop()

    records = read_records(log_dir)
    by_id = {r["request_id"]: r for r in records}
    problems = []
    if len(records) != 20:
        problems.append(f"{len(records)} records for 20 requests")
    ok = 0
    for label, resp in sent:
        rec = by_id.get(resp["request_id"])
        if rec is None:
            problems.append(f"{label}: no record for status {resp['status']}")
            continue
        missing = [f for f in FIELDS if f not in rec]
        if missing:
            problems.append(f"{label}: missing {missing}")
        elif rec["status_code"] != resp["status"]:
            problems.append(f"{label}: logged {rec['status_code']}, client saw {resp['status']}")
        elif rec["duration_ms"] is None:
            problems.append(f"{label}: duration_ms is null")
        else:
            ok += 1
    flood = [r["status"] for l, r in sent if l.startswith("flood")]
    if flood != [200] * 5 + [429]:
        problems.append(f"flood statuses were {flood}")
    met = ok == 20 and not problems
    return f"{ok}/20 complete", met, {
        "client_statuses": [(l, r["status"]) for l, r in sent],
        "problems": problems, "n_records": len(records),
        "sample_records": records[8:14] + records[-2:],
    }


def crit2(log_dir: Path):
    results = []
    for k in range(3):
        d = log_dir / f"start{k+1}"
        t_launch = time.perf_counter()
        svc = Service(d)
        try:
            svc.ready()
            ready_s = time.perf_counter() - t_launch
            r = submit({"text": text_of(100, k), "creator_id": f"c2_{k}"})
        finally:
            svc.stop()
        results.append({"start": k + 1, "ready_s": round(ready_s, 2),
                        "first_submit_s": round(r["ms"] / 1000, 2), "status": r["status"]})
    good = [x for x in results if x["status"] == 200 and x["first_submit_s"] <= 3.0]
    worst = max(x["first_submit_s"] for x in results)
    return f"{len(good)}/3 (worst {worst:.1f}s)", len(good) == 3, {"starts": results}


def crit3(log_dir: Path):
    svc = Service(log_dir)
    times = []
    try:
        svc.ready()
        submit({"text": text_of(100), "creator_id": "c3_warmup"})   # load the model; not timed
        plan = [100] * 8 + [250] * 6 + [600] * 6
        for i, n in enumerate(plan):
            r = submit({"text": text_of(n, i), "creator_id": f"c3_{i}"})
            times.append((n, r["status"], r["ms"] / 1000))
    finally:
        svc.stop()
    secs = sorted(t for _, _, t in times)
    p95, worst = secs[18], secs[-1]
    all_ok = all(s == 200 for _, s, _ in times)
    met = all_ok and p95 <= 0.5 and worst <= 1.5
    by_len = {n: round(statistics.mean(t for m, _, t in times if m == n), 3) for n in (100, 250, 600)}
    return f"p95 {p95:.2f}s, max {worst:.2f}s", met, {
        "p95_s": round(p95, 3), "max_s": round(worst, 3), "median_s": round(statistics.median(secs), 3),
        "mean_s_by_words": by_len, "all_200": all_ok,
    }


def crit4(log_dir: Path):
    svc = Service(log_dir, extra_env={"AI201_DETECTOR_MODEL": "no-such-model-capstone",
                                      "HF_HUB_OFFLINE": "1"})
    try:
        svc.ready()
        rs = [submit({"text": text_of(60, i), "creator_id": f"c4_{i}"}, timeout=30) for i in range(5)]
        ping = requests.post(f"{URL}/ping", json={"message": "x"}, timeout=10).status_code
        health = requests.get(f"{URL}/health", timeout=10).status_code
    finally:
        svc.stop()
    records = read_records(log_dir)
    by_id = {r["request_id"]: r for r in records}
    good = 0
    for r in rs:
        rec = by_id.get(r["request_id"], {})
        if (r["status"] == 503 and r["json"].get("error") == "detector_unavailable"
                and r["ms"] <= 5000 and rec.get("outcome") == "error"
                and rec.get("reason") == "detector_unavailable"):
            good += 1
    met = good == 5 and ping == 200 and health == 200
    return f"{good}/5 (ping {ping}, health {health})", met, {
        "statuses": [r["status"] for r in rs],
        "ms": [round(r["ms"]) for r in rs],
        "bodies": [r["json"] for r in rs[:2]],
        "sample_records": records[:2],
    }


def crit5(log_dir: Path):
    odd = {
        "no punctuation": " ".join(text_of(100).replace(".", "").replace(",", "").split()),
        "one 3000-char word": "a b c d " + "x" * 3000,
        "60 emoji": " ".join(["\U0001F600"] * 60),
        "arabic paragraph": " ".join(["هذا نص قصير مكتوب باللغة العربية لاختبار النظام"] * 3),
        "word x200": "hello " * 200,
        "newlines and tabs": "\n".join("word\t\tword" for _ in range(40)),
    }
    svc = Service(log_dir)
    out = {}
    try:
        svc.ready()
        submit({"text": text_of(100), "creator_id": "c5_warmup"})
        for i, (name, text) in enumerate(odd.items()):
            r = submit({"text": text, "creator_id": f"c5_{i}"})
            j = r["json"]
            nums = [j.get(k) for k in ("model_score", "style_score", "confidence")]
            good = (r["status"] == 200 and r["ms"] <= 5000
                    and all(isinstance(n, (int, float)) and 0 <= n <= 1 for n in nums))
            out[name] = {"status": r["status"], "seconds": round(r["ms"] / 1000, 2),
                         "scores": nums, "ok": good}
    finally:
        svc.stop()
    n_ok = sum(v["ok"] for v in out.values())
    return f"{n_ok}/6", n_ok == 6, out


CRITERIA = [
    (1, "Every /submit call leaves a complete record", "20 of 20, every trial", crit1),
    (2, "First request after restart ≤ 3.0 s", "3 of 3 starts, every trial", crit2),
    (3, "Warm p95 ≤ 0.5 s, none > 1.5 s", "p95 ≤ 0.5 s, every trial", crit3),
    (4, "Model unavailable → clean 503, logged, service stays up", "5 of 5, every trial", crit4),
    (5, "Odd but valid text never crashes", "6 of 6, every trial", crit5),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--trials", type=int, default=3)
    args = ap.parse_args()

    base = ROOT / "logs" / f"capstone_{args.label}"
    rows = {num: [] for num, *_ in CRITERIA}
    raw = {num: [] for num, *_ in CRITERIA}
    for trial in range(1, args.trials + 1):
        print(f"\n=== trial {trial} ===")
        for num, name, target, fn in CRITERIA:
            cell, met, detail = fn(base / f"trial{trial}_c{num}")
            rows[num].append((cell, met))
            raw[num].append(detail)
            print(f"  criterion {num}: {cell}  -> {'met' if met else 'MISSED'}")

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    path = out / f"capstone_{args.label}.md"
    heads = " | ".join(f"Run {i}" for i in range(1, args.trials + 1))
    lines = [
        f"# Capstone run log — {args.label}", "",
        f"- Produced by: `run_capstone.py::main` · {dt.datetime.now():%Y-%m-%d %H:%M}",
        "- Service under test: `app.py` (hooks) + `telemetry.py`; logs in "
        f"`logs/capstone_{args.label}/`", "",
        f"| Criterion | Target | {heads} | Verdict |",
        "|---|---|" + "|".join(["---"] * args.trials) + "|---|",
    ]
    for num, name, target, _ in CRITERIA:
        cells = " | ".join(("✓ " if m else "✗ ") + c for c, m in rows[num])
        verdict = "MET" if all(m for _, m in rows[num]) else "MISSED"
        lines.append(f"| {num}. {name} | {target} | {cells} | {verdict} |")
    lines += ["", "(✓ = that trial met the target, ✗ = it did not.)", "", "---", "",
              "## What actually came back", ""]
    for num, name, _, _ in CRITERIA:
        lines += [f"### Criterion {num} — {name}", ""]
        for t, d in enumerate(raw[num], 1):
            lines += [f"**Trial {t}** (`run_capstone.py::crit{num}`)", "", "```json",
                      json.dumps(d, indent=2, ensure_ascii=False), "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
