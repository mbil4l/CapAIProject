# Capstone run log — after

- Produced by: `run_capstone.py::main` · 2026-11-10 04:14
- Service under test: `app.py` (hooks) + `telemetry.py`; logs in `logs/capstone_after/`

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every /submit call leaves a complete record | 20 of 20, every trial | ✓ 20/20 complete | ✓ 20/20 complete | ✓ 20/20 complete | MET |
| 2. First request after restart ≤ 3.0 s | 3 of 3 starts, every trial | ✓ 3/3 (worst 0.3s) | ✓ 3/3 (worst 0.3s) | ✓ 3/3 (worst 0.3s) | MET |
| 3. Warm p95 ≤ 0.5 s, none > 1.5 s | p95 ≤ 0.5 s, every trial | ✓ p95 0.25s, max 0.28s | ✓ p95 0.28s, max 0.30s | ✓ p95 0.28s, max 0.30s | MET |
| 4. Model unavailable → clean 503, logged, service stays up | 5 of 5, every trial | ✓ 5/5 (ping 200, health 200) | ✓ 5/5 (ping 200, health 200) | ✓ 5/5 (ping 200, health 200) | MET |
| 5. Odd but valid text never crashes | 6 of 6, every trial | ✓ 6/6 | ✓ 6/6 | ✓ 6/6 | MET |

(✓ = that trial met the target, ✗ = it did not.)

---

## What actually came back

### Criterion 1 — Every /submit call leaves a complete record

**Trial 1** (`run_capstone.py::crit1`)

```json
{
  "client_statuses": [
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "no text",
      400
    ],
    [
      "empty text",
      400
    ],
    [
      "null text",
      400
    ],
    [
      "numeric text",
      400
    ],
    [
      "too long",
      413
    ],
    [
      "json list",
      400
    ],
    [
      "flood 1",
      200
    ],
    [
      "flood 2",
      200
    ],
    [
      "flood 3",
      200
    ],
    [
      "flood 4",
      200
    ],
    [
      "flood 5",
      200
    ],
    [
      "flood 6",
      429
    ]
  ],
  "problems": [],
  "n_records": 20,
  "sample_records": [
    {
      "timestamp": "2026-11-10T09:12:17+00:00",
      "request_id": "e2c5b92a1746",
      "route": "/submit",
      "creator_id": "c1_bad_1",
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.7,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:17+00:00",
      "request_id": "d40940346154",
      "route": "/submit",
      "creator_id": "c1_bad_2",
      "text_type": "str",
      "text_chars": 0,
      "text_hash": "e3b0c44298fc",
      "status_code": 400,
      "outcome": "rejected",
      "reason": "text_too_short",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.6,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:17+00:00",
      "request_id": "fe8766a5af64",
      "route": "/submit",
      "creator_id": "c1_bad_3",
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.9,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:17+00:00",
      "request_id": "c17de7d160fb",
      "route": "/submit",
      "creator_id": "c1_bad_4",
      "text_type": "int",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.2,
      "cpu_ms": 218.8,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:17+00:00",
      "request_id": "e111f1da8136",
      "route": "/submit",
      "creator_id": "c1_long",
      "text_type": "str",
      "text_chars": 25000,
      "text_hash": "022625a9ba7a",
      "status_code": 413,
      "outcome": "rejected",
      "reason": "text_too_long",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.9,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:17+00:00",
      "request_id": "d07adbdad3da",
      "route": "/submit",
      "creator_id": null,
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_json",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.7,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:17+00:00",
      "request_id": "43a1569cdc2e",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 301,
      "text_hash": "566a00236ffa",
      "status_code": 200,
      "outcome": "decided",
      "reason": null,
      "content_id": "9a52571430e2",
      "guess": "unsure",
      "confidence": 0.532,
      "model_score": 0.5016,
      "style_score": 0.5624,
      "duration_ms": 67.3,
      "cpu_ms": 1062.5,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:17+00:00",
      "request_id": "34f5b91ca6a2",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 302,
      "text_hash": "ee1c0a194b00",
      "status_code": 429,
      "outcome": "rate_limited",
      "reason": "rate_limited",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.0,
      "cpu_ms": 0.0,
      "detector_cold": false
    }
  ]
}
```

**Trial 2** (`run_capstone.py::crit1`)

```json
{
  "client_statuses": [
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "no text",
      400
    ],
    [
      "empty text",
      400
    ],
    [
      "null text",
      400
    ],
    [
      "numeric text",
      400
    ],
    [
      "too long",
      413
    ],
    [
      "json list",
      400
    ],
    [
      "flood 1",
      200
    ],
    [
      "flood 2",
      200
    ],
    [
      "flood 3",
      200
    ],
    [
      "flood 4",
      200
    ],
    [
      "flood 5",
      200
    ],
    [
      "flood 6",
      429
    ]
  ],
  "problems": [],
  "n_records": 20,
  "sample_records": [
    {
      "timestamp": "2026-11-10T09:12:53+00:00",
      "request_id": "58761875edaf",
      "route": "/submit",
      "creator_id": "c1_bad_1",
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.9,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:53+00:00",
      "request_id": "f4e1f273e48e",
      "route": "/submit",
      "creator_id": "c1_bad_2",
      "text_type": "str",
      "text_chars": 0,
      "text_hash": "e3b0c44298fc",
      "status_code": 400,
      "outcome": "rejected",
      "reason": "text_too_short",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.6,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:53+00:00",
      "request_id": "f8499643b60a",
      "route": "/submit",
      "creator_id": "c1_bad_3",
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.7,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:53+00:00",
      "request_id": "500884a6d09c",
      "route": "/submit",
      "creator_id": "c1_bad_4",
      "text_type": "int",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.6,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:53+00:00",
      "request_id": "7eadbf52d3ad",
      "route": "/submit",
      "creator_id": "c1_long",
      "text_type": "str",
      "text_chars": 25000,
      "text_hash": "022625a9ba7a",
      "status_code": 413,
      "outcome": "rejected",
      "reason": "text_too_long",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.2,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:53+00:00",
      "request_id": "86124a37ce71",
      "route": "/submit",
      "creator_id": null,
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_json",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.3,
      "cpu_ms": 265.6,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:53+00:00",
      "request_id": "a59e6e246714",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 301,
      "text_hash": "566a00236ffa",
      "status_code": 200,
      "outcome": "decided",
      "reason": null,
      "content_id": "4d20dd2df779",
      "guess": "unsure",
      "confidence": 0.532,
      "model_score": 0.5016,
      "style_score": 0.5624,
      "duration_ms": 71.9,
      "cpu_ms": 1046.9,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:12:53+00:00",
      "request_id": "932d3ddbb7f9",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 302,
      "text_hash": "ee1c0a194b00",
      "status_code": 429,
      "outcome": "rate_limited",
      "reason": "rate_limited",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.2,
      "cpu_ms": 0.0,
      "detector_cold": false
    }
  ]
}
```

**Trial 3** (`run_capstone.py::crit1`)

```json
{
  "client_statuses": [
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "valid",
      200
    ],
    [
      "no text",
      400
    ],
    [
      "empty text",
      400
    ],
    [
      "null text",
      400
    ],
    [
      "numeric text",
      400
    ],
    [
      "too long",
      413
    ],
    [
      "json list",
      400
    ],
    [
      "flood 1",
      200
    ],
    [
      "flood 2",
      200
    ],
    [
      "flood 3",
      200
    ],
    [
      "flood 4",
      200
    ],
    [
      "flood 5",
      200
    ],
    [
      "flood 6",
      429
    ]
  ],
  "problems": [],
  "n_records": 20,
  "sample_records": [
    {
      "timestamp": "2026-11-10T09:13:30+00:00",
      "request_id": "782bb631e068",
      "route": "/submit",
      "creator_id": "c1_bad_1",
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.9,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:13:30+00:00",
      "request_id": "b6294ac51c62",
      "route": "/submit",
      "creator_id": "c1_bad_2",
      "text_type": "str",
      "text_chars": 0,
      "text_hash": "e3b0c44298fc",
      "status_code": 400,
      "outcome": "rejected",
      "reason": "text_too_short",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.5,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:13:30+00:00",
      "request_id": "c50a969184d3",
      "route": "/submit",
      "creator_id": "c1_bad_3",
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.5,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:13:30+00:00",
      "request_id": "5c6dc3308a68",
      "route": "/submit",
      "creator_id": "c1_bad_4",
      "text_type": "int",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_text",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.5,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:13:30+00:00",
      "request_id": "3e08643fe13f",
      "route": "/submit",
      "creator_id": "c1_long",
      "text_type": "str",
      "text_chars": 25000,
      "text_hash": "022625a9ba7a",
      "status_code": 413,
      "outcome": "rejected",
      "reason": "text_too_long",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.2,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:13:30+00:00",
      "request_id": "637fee2cbe68",
      "route": "/submit",
      "creator_id": null,
      "text_type": "NoneType",
      "text_chars": null,
      "text_hash": null,
      "status_code": 400,
      "outcome": "rejected",
      "reason": "bad_json",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.7,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:13:31+00:00",
      "request_id": "427ad76acd25",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 301,
      "text_hash": "566a00236ffa",
      "status_code": 200,
      "outcome": "decided",
      "reason": null,
      "content_id": "b7bb5694e703",
      "guess": "unsure",
      "confidence": 0.532,
      "model_score": 0.5016,
      "style_score": 0.5624,
      "duration_ms": 77.0,
      "cpu_ms": 1203.1,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:13:31+00:00",
      "request_id": "f4e6031c526c",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 302,
      "text_hash": "ee1c0a194b00",
      "status_code": 429,
      "outcome": "rate_limited",
      "reason": "rate_limited",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.8,
      "cpu_ms": 0.0,
      "detector_cold": false
    }
  ]
}
```

### Criterion 2 — First request after restart ≤ 3.0 s

**Trial 1** (`run_capstone.py::crit2`)

```json
{
  "starts": [
    {
      "start": 1,
      "ready_s": 3.71,
      "first_submit_s": 0.27,
      "status": 200
    },
    {
      "start": 2,
      "ready_s": 3.71,
      "first_submit_s": 0.25,
      "status": 200
    },
    {
      "start": 3,
      "ready_s": 3.71,
      "first_submit_s": 0.28,
      "status": 200
    }
  ]
}
```

**Trial 2** (`run_capstone.py::crit2`)

```json
{
  "starts": [
    {
      "start": 1,
      "ready_s": 3.72,
      "first_submit_s": 0.3,
      "status": 200
    },
    {
      "start": 2,
      "ready_s": 3.71,
      "first_submit_s": 0.27,
      "status": 200
    },
    {
      "start": 3,
      "ready_s": 3.71,
      "first_submit_s": 0.3,
      "status": 200
    }
  ]
}
```

**Trial 3** (`run_capstone.py::crit2`)

```json
{
  "starts": [
    {
      "start": 1,
      "ready_s": 3.71,
      "first_submit_s": 0.32,
      "status": 200
    },
    {
      "start": 2,
      "ready_s": 3.71,
      "first_submit_s": 0.32,
      "status": 200
    },
    {
      "start": 3,
      "ready_s": 3.72,
      "first_submit_s": 0.3,
      "status": 200
    }
  ]
}
```

### Criterion 3 — Warm p95 ≤ 0.5 s, none > 1.5 s

**Trial 1** (`run_capstone.py::crit3`)

```json
{
  "p95_s": 0.254,
  "max_s": 0.281,
  "median_s": 0.169,
  "mean_s_by_words": {
    "100": 0.092,
    "250": 0.188,
    "600": 0.246
  },
  "all_200": true
}
```

**Trial 2** (`run_capstone.py::crit3`)

```json
{
  "p95_s": 0.284,
  "max_s": 0.295,
  "median_s": 0.186,
  "mean_s_by_words": {
    "100": 0.102,
    "250": 0.202,
    "600": 0.26
  },
  "all_200": true
}
```

**Trial 3** (`run_capstone.py::crit3`)

```json
{
  "p95_s": 0.28,
  "max_s": 0.298,
  "median_s": 0.19,
  "mean_s_by_words": {
    "100": 0.099,
    "250": 0.207,
    "600": 0.264
  },
  "all_200": true
}
```

### Criterion 4 — Model unavailable → clean 503, logged, service stays up

**Trial 1** (`run_capstone.py::crit4`)

```json
{
  "statuses": [
    503,
    503,
    503,
    503,
    503
  ],
  "ms": [
    6,
    3,
    2,
    2,
    2
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
  ],
  "sample_records": [
    {
      "timestamp": "2026-11-10T09:12:42+00:00",
      "request_id": "f0b50ebf9641",
      "route": "/submit",
      "creator_id": "c4_0",
      "text_type": "str",
      "text_chars": 292,
      "text_hash": "cc09c9587a5f",
      "status_code": 503,
      "outcome": "error",
      "reason": "detector_unavailable",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.1,
      "cpu_ms": 0.0,
      "detector_cold": true
    },
    {
      "timestamp": "2026-11-10T09:12:42+00:00",
      "request_id": "5098b38ab5f6",
      "route": "/submit",
      "creator_id": "c4_1",
      "text_type": "str",
      "text_chars": 298,
      "text_hash": "45ef6eb5ac5e",
      "status_code": 503,
      "outcome": "error",
      "reason": "detector_unavailable",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.9,
      "cpu_ms": 0.0,
      "detector_cold": true
    }
  ]
}
```

**Trial 2** (`run_capstone.py::crit4`)

```json
{
  "statuses": [
    503,
    503,
    503,
    503,
    503
  ],
  "ms": [
    6,
    3,
    2,
    12,
    11
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
  ],
  "sample_records": [
    {
      "timestamp": "2026-11-10T09:13:19+00:00",
      "request_id": "c4a8e3eb955d",
      "route": "/submit",
      "creator_id": "c4_0",
      "text_type": "str",
      "text_chars": 292,
      "text_hash": "cc09c9587a5f",
      "status_code": 503,
      "outcome": "error",
      "reason": "detector_unavailable",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.3,
      "cpu_ms": 0.0,
      "detector_cold": true
    },
    {
      "timestamp": "2026-11-10T09:13:19+00:00",
      "request_id": "fab2d03f3807",
      "route": "/submit",
      "creator_id": "c4_1",
      "text_type": "str",
      "text_chars": 298,
      "text_hash": "45ef6eb5ac5e",
      "status_code": 503,
      "outcome": "error",
      "reason": "detector_unavailable",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.8,
      "cpu_ms": 0.0,
      "detector_cold": true
    }
  ]
}
```

**Trial 3** (`run_capstone.py::crit4`)

```json
{
  "statuses": [
    503,
    503,
    503,
    503,
    503
  ],
  "ms": [
    7,
    3,
    13,
    13,
    2
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
  ],
  "sample_records": [
    {
      "timestamp": "2026-11-10T09:13:56+00:00",
      "request_id": "d7cee6b201d6",
      "route": "/submit",
      "creator_id": "c4_0",
      "text_type": "str",
      "text_chars": 292,
      "text_hash": "cc09c9587a5f",
      "status_code": 503,
      "outcome": "error",
      "reason": "detector_unavailable",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 1.3,
      "cpu_ms": 0.0,
      "detector_cold": true
    },
    {
      "timestamp": "2026-11-10T09:13:56+00:00",
      "request_id": "1baf00daa907",
      "route": "/submit",
      "creator_id": "c4_1",
      "text_type": "str",
      "text_chars": 298,
      "text_hash": "45ef6eb5ac5e",
      "status_code": 503,
      "outcome": "error",
      "reason": "detector_unavailable",
      "content_id": null,
      "guess": null,
      "confidence": null,
      "model_score": null,
      "style_score": null,
      "duration_ms": 0.9,
      "cpu_ms": 15.6,
      "detector_cold": true
    }
  ]
}
```

### Criterion 5 — Odd but valid text never crashes

**Trial 1** (`run_capstone.py::crit5`)

```json
{
  "no punctuation": {
    "status": 200,
    "seconds": 0.08,
    "scores": [
      0.3753,
      0.6293,
      0.5023
    ],
    "ok": true
  },
  "one 3000-char word": {
    "status": 200,
    "seconds": 0.27,
    "scores": [
      0.997,
      0.575,
      0.643
    ],
    "ok": true
  },
  "60 emoji": {
    "status": 200,
    "seconds": 0.08,
    "scores": [
      0.9971,
      0.725,
      0.861
    ],
    "ok": true
  },
  "arabic paragraph": {
    "status": 200,
    "seconds": 0.15,
    "scores": [
      0.991,
      0.725,
      0.858
    ],
    "ok": true
  },
  "word x200": {
    "status": 200,
    "seconds": 0.16,
    "scores": [
      0.997,
      0.725,
      0.861
    ],
    "ok": true
  },
  "newlines and tabs": {
    "status": 200,
    "seconds": 0.17,
    "scores": [
      0.0,
      0.725,
      0.4313
    ],
    "ok": true
  }
}
```

**Trial 2** (`run_capstone.py::crit5`)

```json
{
  "no punctuation": {
    "status": 200,
    "seconds": 0.09,
    "scores": [
      0.3753,
      0.6293,
      0.5023
    ],
    "ok": true
  },
  "one 3000-char word": {
    "status": 200,
    "seconds": 0.25,
    "scores": [
      0.997,
      0.575,
      0.643
    ],
    "ok": true
  },
  "60 emoji": {
    "status": 200,
    "seconds": 0.08,
    "scores": [
      0.9971,
      0.725,
      0.861
    ],
    "ok": true
  },
  "arabic paragraph": {
    "status": 200,
    "seconds": 0.12,
    "scores": [
      0.991,
      0.725,
      0.858
    ],
    "ok": true
  },
  "word x200": {
    "status": 200,
    "seconds": 0.14,
    "scores": [
      0.997,
      0.725,
      0.861
    ],
    "ok": true
  },
  "newlines and tabs": {
    "status": 200,
    "seconds": 0.17,
    "scores": [
      0.0,
      0.725,
      0.4313
    ],
    "ok": true
  }
}
```

**Trial 3** (`run_capstone.py::crit5`)

```json
{
  "no punctuation": {
    "status": 200,
    "seconds": 0.09,
    "scores": [
      0.3753,
      0.6293,
      0.5023
    ],
    "ok": true
  },
  "one 3000-char word": {
    "status": 200,
    "seconds": 0.28,
    "scores": [
      0.997,
      0.575,
      0.643
    ],
    "ok": true
  },
  "60 emoji": {
    "status": 200,
    "seconds": 0.11,
    "scores": [
      0.9971,
      0.725,
      0.861
    ],
    "ok": true
  },
  "arabic paragraph": {
    "status": 200,
    "seconds": 0.11,
    "scores": [
      0.991,
      0.725,
      0.858
    ],
    "ok": true
  },
  "word x200": {
    "status": 200,
    "seconds": 0.15,
    "scores": [
      0.997,
      0.725,
      0.861
    ],
    "ok": true
  },
  "newlines and tabs": {
    "status": 200,
    "seconds": 0.15,
    "scores": [
      0.0,
      0.725,
      0.4313
    ],
    "ok": true
  }
}
```
