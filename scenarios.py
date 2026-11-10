"""
What my five criteria are tested with. run_eval.py runs everything here three
times.

Criteria 1-3 send texts and read the labels and scores that come back. 4 and 5
need more than that (an appeal needs a content_id from an earlier submission; a
bad-input check needs to look in the log), so those two have a `runner` that
talks to the service itself. Every scenario has a `judge` that applies the
target from criteria.md to one trial and says pass or fail. The target is copied
into each scenario, word for word in spirit, so the judge isn't a second opinion
about what the criterion meant.

The texts for 2, 3 and 4 are invented fixtures, not my own writing. Criterion 1
needs real writing of mine, so it reads `my_writing.txt`.
"""

from pathlib import Path

import config
import scoring

ROOT = Path(__file__).parent


# ── Criterion 1: my own writing ──────────────────────────────────────────────
# my_writing.txt holds ten pieces I wrote myself, separated by a line that is
# just `---`. A piece that starts with `[plain]` on its own line is one I'd call
# plain writing (short sentences, everyday words). Criterion 1 needs at least 4.

def load_my_writing() -> tuple[list[str], int]:
    path = ROOT / "my_writing.txt"
    if not path.exists():
        return ["REPLACE ME: put ten pieces of your own writing in my_writing.txt"], 0
    pieces, plain = [], 0
    for block in path.read_text(encoding="utf-8").split("\n---\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if lines[0].strip().lower() == "[plain]":
            plain += 1
            block = "\n".join(lines[1:]).strip()
        pieces.append(block)
    return pieces, plain


MY_WRITING, MY_PLAIN_COUNT = load_my_writing()


def judge_own_writing(results):
    flagged = sum(1 for r in results if r.get("guess") == "ai")
    scores = [r["confidence"] for r in results if r.get("confidence") is not None]
    top = max(scores) if scores else 0.0
    ok = (
        len(results) == 10
        and len(scores) == 10
        and flagged <= 1
        and top <= 0.80
        and MY_PLAIN_COUNT >= 4
    )
    return ok, f"{flagged}/10 flagged AI, top score {top:.2f}, {MY_PLAIN_COUNT} plain"


# ── Criterion 2: clearly AI and clearly human text score apart ───────────────
# Invented fixtures: five obviously AI-style paragraphs, five obviously human
# ones. First five are AI, last five are human; judge_spread relies on that.

AI_TEXTS = [
    "In today's fast-paced world, time management has become an essential skill "
    "for professionals across all industries. By prioritizing tasks effectively, "
    "individuals can significantly improve their productivity and reduce stress. "
    "Furthermore, leveraging digital tools such as calendars and task managers can "
    "streamline workflows and foster greater accountability. Ultimately, mastering "
    "time management is a key factor in achieving long-term career success and "
    "overall well-being.",

    "Climate change represents one of the most significant challenges facing "
    "humanity in the twenty-first century. Rising global temperatures contribute to "
    "more frequent extreme weather events, threatening ecosystems and communities "
    "worldwide. It is therefore crucial that governments, businesses, and "
    "individuals work together to implement sustainable solutions. By embracing "
    "renewable energy and reducing emissions, we can create a more resilient and "
    "equitable future for generations to come.",

    "Regular exercise offers a wide range of benefits for both physical and mental "
    "health. Engaging in consistent physical activity can improve cardiovascular "
    "fitness, strengthen muscles, and boost overall energy levels. Additionally, "
    "exercise plays a vital role in reducing anxiety and enhancing mood. To "
    "maximize these benefits, it is important to establish a balanced routine that "
    "incorporates cardio, strength training, and adequate rest.",

    "Artificial intelligence is transforming the way organizations approach "
    "decision-making and innovation. Machine learning models can analyze vast "
    "amounts of data to uncover patterns that would otherwise remain hidden. "
    "Moreover, automation of routine tasks allows employees to focus on "
    "higher-value work. However, it is essential to consider ethical implications "
    "and ensure that these technologies are deployed responsibly and transparently.",

    "Effective leadership requires a combination of vision, empathy, and strong "
    "communication skills. Leaders who foster a culture of trust and collaboration "
    "empower their teams to perform at their best. Furthermore, providing "
    "constructive feedback and recognizing achievements can significantly boost "
    "morale. By cultivating these qualities, leaders can navigate challenges "
    "successfully and drive sustainable growth for their organizations.",
]

HUMAN_TEXTS = [
    "My brother borrowed the van in March and I haven't seen it since. He says it's "
    "\"at a friend's.\" Which friend? No idea. Mum keeps asking and I keep shrugging, "
    "because honestly, what do I know - he's twenty-six, not six. Still. A van.",

    "We never did fix the gate. It dragged on the gravel every single time, that "
    "long scraping groan, and after a while you stopped hearing it. Then Dad sold "
    "the house and the new people put in an electric one, and I stood at the end of "
    "the lane thinking: huh, quiet.",

    "Ran out of milk, so, black tea for a week. Weirdly fine. The cat disagrees. She "
    "stared at the empty fridge shelf like I'd personally wronged her; I mean, I "
    "had, but still.",

    "The interview was a mess! Wrong building first, then the lift broke, then a "
    "woman called Pauline asked me to describe a time I'd failed and I just... "
    "laughed. Out loud. She laughed too, thank god. Got the job, weirdly.",

    "Nobody tells you how loud a newborn is at 3 a.m. Not the crying - the small "
    "noises, the snuffling, the little cough that makes you sit bolt upright. I lay "
    "there for an hour last night listening to her breathe. Ridiculous. Wonderful, "
    "though.",
]


def _confidences(results):
    return [r.get("confidence") for r in results]


def judge_spread(results):
    conf = _confidences(results)
    if len(conf) != 10 or any(c is None for c in conf):
        return False, "some submissions failed"
    ai, human = conf[:5], conf[5:]
    gap = sum(ai) / 5 - sum(human) / 5
    separated = min(ai) > max(human)
    ok = gap >= 0.30 and separated
    return ok, (f"gap {gap:.2f}, lowest AI {min(ai):.2f} vs highest human "
                f"{max(human):.2f}")


# ── Criterion 3: all three labels are reachable ──────────────────────────────
# Ten inputs chosen before looking at any scores: some obviously AI, some
# obviously human, and four that sit in between (lightly edited AI, AI chopped
# into uneven sentences, plain ordinary prose, formal human prose).

COVERAGE_TEXTS = [
    AI_TEXTS[0], AI_TEXTS[1], AI_TEXTS[2],
    HUMAN_TEXTS[0], HUMAN_TEXTS[1], HUMAN_TEXTS[2],
    "In today's rapidly evolving digital world, good communication is essential for "
    "building succesful teams. Companies that prioritize collaboration are better "
    "placed to hit their goals. Using the right tools can really boost "
    "productivity. It's important to note that clear expectations and regular "
    "feedback play a big role in employee engagement. Embrace these practices, and "
    "companies can build a more cohesive workplace.",
    "Communication matters. In a digital landscape that keeps evolving, teams that "
    "prioritize collaboration are simply better positioned to achieve their goals, "
    "and leveraging the right tools - which is important to note - can "
    "significantly enhance productivity. Feedback? Regular. Expectations? Clear. "
    "They play a crucial role in employee engagement; by embracing these best "
    "practices, companies can create a cohesive workplace.",
    "I woke up late today. I made some coffee and checked my phone. Then I walked "
    "to the store to get milk and bread. The store was busy because it was "
    "Saturday. I came home and made a sandwich for lunch. After that I watched a "
    "movie with my brother.",
    "The committee's report, issued in March after eighteen months of hearings, "
    "concluded that the existing statute had failed to anticipate the "
    "consolidation of regional carriers. Its authors, while divided on remedy, "
    "agreed on diagnosis: enforcement had lagged the market, and the agency's "
    "discretionary powers, never intended to bear such weight, had been stretched "
    "past usefulness. Whether Parliament will act remains, as ever, uncertain.",
]


def judge_coverage(results):
    seen = {r.get("guess") for r in results} & {"human", "unsure", "ai"}

    # The checks that don't need the service: every score maps to exactly one
    # label, the unsure band is wide enough, and 0.51 and 0.95 differ.
    swept = {scoring.score_to_label(i / 1000)[0] for i in range(1001)}
    band = config.AI_THRESHOLD - config.HUMAN_THRESHOLD
    differ = scoring.score_to_label(0.51)[0] != scoring.score_to_label(0.95)[0]
    static_ok = swept == {"human", "unsure", "ai"} and band >= 0.25 and differ

    ok = len(results) == 10 and seen == {"human", "unsure", "ai"} and static_ok
    counts = {g: sum(1 for r in results if r.get("guess") == g) for g in ("human", "unsure", "ai")}
    return ok, (f"{len(seen)}/3 labels (human {counts['human']}, unsure "
                f"{counts['unsure']}, ai {counts['ai']}), unsure band {band:.2f}, "
                f"0.51 vs 0.95 {'differ' if differ else 'same'}")


# ── Criterion 4: an appeal always changes status and is always recorded ──────

APPEAL_TEXTS = AI_TEXTS + HUMAN_TEXTS


def _post(requests, url, path, body, timeout):
    try:
        r = requests.post(f"{url}{path}", json=body, timeout=timeout)
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            data = {}
        return r.status_code, data
    except Exception as exc:  # noqa: BLE001
        return None, {"error": f"{type(exc).__name__}: {exc}"}


def _log(requests, url, timeout):
    return requests.get(f"{url}/log", timeout=timeout).json()["entries"]


def run_appeals(url, requests, timeout):
    """Ten submissions, an appeal against each, then two appeals that should be refused."""
    items = []
    for i, text in enumerate(APPEAL_TEXTS, 1):
        s_status, s = _post(requests, url, "/submit",
                            {"text": text, "creator_id": f"eval_appeal_{i}"}, timeout)
        reasoning = f"eval appeal {i}: I wrote this myself."
        item = {"sent": text[:60], "submit_status": s_status,
                "content_id": s.get("content_id"), "reasoning": reasoning}
        if s.get("content_id"):
            a_status, a = _post(requests, url, "/appeal",
                                {"content_id": s["content_id"], "reasoning": reasoning}, timeout)
            item.update(appeal_status=a_status, appeal_body_status=a.get("status"))
        items.append(item)

    entries = _log(requests, url, timeout)
    for item in items:
        cid = item["content_id"]
        mine = [e for e in entries if cid and e.get("content_id") == cid]
        decisions = [e for e in mine if e.get("event") is None]
        appeals = [e for e in mine if e.get("event") == "appeal"]
        item["decision_entries"] = len(decisions)
        item["decision_still_decided"] = bool(decisions) and all(
            d.get("status") == "decided" for d in decisions)
        item["appeal_entries"] = len(appeals)
        item["appeal_recorded"] = any(
            e.get("reasoning") == item["reasoning"] and e.get("status") == "under_review"
            for e in appeals)

    # Appeals that should be refused. Nothing about an appeal should be written.
    appeals_before = sum(1 for e in entries if e.get("event") == "appeal")
    total_before = len(entries)
    real_id = next((it["content_id"] for it in items if it["content_id"]), "x")
    bad = [
        ("unknown content_id", {"content_id": "eval_no_such_id", "reasoning": "typo"}),
        ("blank reasoning", {"content_id": real_id, "reasoning": "   "}),
    ]
    refused = []
    for name, body in bad:
        status, data = _post(requests, url, "/appeal", body, timeout)
        refused.append({"negative": name, "status": status, "error": data.get("error")})
    after = _log(requests, url, timeout)
    refused.append({
        "negative": "log after the two refused appeals",
        "appeal_entries_added": sum(1 for e in after if e.get("event") == "appeal") - appeals_before,
        "entries_added": len(after) - total_before,
        "entries": [e for e in after[total_before:]],
    })
    return items + refused


def judge_appeals(results):
    positives = [r for r in results if "negative" not in r]
    good = sum(
        1 for r in positives
        if r.get("submit_status") == 200 and r.get("appeal_status") == 200
        and r.get("appeal_body_status") == "under_review"
        and r.get("appeal_recorded") and r.get("decision_entries") == 1
        and r.get("decision_still_decided")
    )
    refused = [r for r in results if r.get("negative") in ("unknown content_id", "blank reasoning")]
    refused_ok = sum(1 for r in refused if isinstance(r.get("status"), int) and 400 <= r["status"] < 500)
    tail = next((r for r in results if str(r.get("negative", "")).startswith("log after")), {})
    appeals_added = tail.get("appeal_entries_added", -1)
    written = tail.get("entries_added", -1)
    ok = good == 10 and refused_ok == 2 and written == 0
    return ok, (f"{good}/10 appeals ok, {refused_ok}/2 bad ones refused with a 4xx, "
                f"{appeals_added} appeal entries and {written} log lines of any kind "
                f"written by them")


# ── Criterion 5: bad input gets a clean refusal, never a crash ───────────────

BAD_BODIES = [
    {"creator_id": "eval_bad_missing"},
    {"text": "", "creator_id": "eval_bad_empty"},
    {"text": "   ", "creator_id": "eval_bad_spaces"},
    {"text": None, "creator_id": "eval_bad_null"},
    {"text": 42, "creator_id": "eval_bad_number"},
    {"text": "word " * 50000, "creator_id": "eval_bad_huge"},
]


def run_bad_input(url, requests, timeout):
    before = [e for e in _log(requests, url, timeout)
              if str(e.get("creator_id", "")).startswith("eval_bad_")
              and e.get("event") == "rejected"]
    results = []
    for body in BAD_BODIES:
        status, data = _post(requests, url, "/submit", body, timeout)
        results.append({"sent": f"{body['creator_id']}: text={str(body.get('text', '<absent>'))[:20]!r}",
                        "status": status, "error": data.get("error")})
    after = [e for e in _log(requests, url, timeout)
             if str(e.get("creator_id", "")).startswith("eval_bad_")
             and e.get("event") == "rejected"]
    ping_status, ping = _post(requests, url, "/ping", {"message": "still up"}, timeout)
    results.append({"after": True, "rejected_entries_added": len(after) - len(before),
                    "ping_status": ping_status, "ping_ok": ping.get("ok")})
    return results


def judge_bad_input(results):
    rows = [r for r in results if "after" not in r]
    tail = next(r for r in results if "after" in r)
    clean = sum(1 for r in rows if r.get("status") in (400, 413) and r.get("error"))
    crashed = sum(1 for r in rows if r.get("status") is None or r["status"] >= 500)
    logged = tail["rejected_entries_added"]
    ok = clean == 6 and crashed == 0 and logged == 6 and tail["ping_ok"] is True
    return ok, (f"{clean}/6 refused cleanly, {crashed} crashed, {logged}/6 logged, "
                f"ping {'ok' if tail['ping_ok'] else 'down'}")


SCENARIOS = [
    {
        "name": "own writing flagged as AI",
        "criterion": 1,
        "target": "at most 1 of 10 flagged AI, none above 0.80, 4+ plain",
        "texts": MY_WRITING,
        "judge": judge_own_writing,
    },
    {
        "name": "clearly AI vs clearly human",
        "criterion": 2,
        "target": "gap of 0.30+, lowest AI above highest human",
        "texts": AI_TEXTS + HUMAN_TEXTS,
        "judge": judge_spread,
    },
    {
        "name": "all three labels reachable",
        "criterion": 3,
        "target": "3 of 3 labels, unsure band 0.25+, 0.51 and 0.95 differ",
        "texts": COVERAGE_TEXTS,
        "judge": judge_coverage,
    },
    {
        "name": "appeal changes status",
        "criterion": 4,
        "target": "10 of 10 appeals ok, refused ones write nothing",
        "runner": run_appeals,
        "judge": judge_appeals,
    },
    {
        "name": "bad input refused cleanly",
        "criterion": 5,
        "target": "6 of 6 refused, none 500, all 6 logged, ping ok",
        "runner": run_bad_input,
        "judge": judge_bad_input,
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A scenario with a `runner` makes its own requests, so it's exempt from the
    texts/bodies checks. A "bodies" scenario is deliberately exempt from the
    empty check.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")
        if scenario.get("runner"):
            continue

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies - pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(f"scenario {i}, body {j} is not a dict")
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(f"scenario {i}, text {j} is empty")
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder - {text}"
                )
        if scenario.get("criterion") == 1 and len(texts) != 10:
            problems.append(f"criterion 1 needs exactly 10 pieces in my_writing.txt, found {len(texts)}")
    return problems
