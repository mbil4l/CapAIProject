# Capstone run log — before

- Produced by: `run_capstone.py::main` · 2026-11-10 04:11
- Service under test: `app.py` (hooks) + `telemetry.py`; logs in `logs/capstone_before/`

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every /submit call leaves a complete record | 20 of 20, every trial | ✓ 20/20 complete | ✓ 20/20 complete | ✓ 20/20 complete | MET |
| 2. First request after restart ≤ 3.0 s | 3 of 3 starts, every trial | ✗ 0/3 (worst 3.5s) | ✗ 0/3 (worst 3.5s) | ✗ 0/3 (worst 3.7s) | MISSED |
| 3. Warm p95 ≤ 0.5 s, none > 1.5 s | p95 ≤ 0.5 s, every trial | ✓ p95 0.24s, max 0.26s | ✓ p95 0.26s, max 0.27s | ✓ p95 0.36s, max 0.48s | MET |
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
      "timestamp": "2026-11-10T09:10:02+00:00",
      "request_id": "cb8262d209bf",
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
      "duration_ms": 1.0,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:02+00:00",
      "request_id": "57994a820fbe",
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
      "duration_ms": 0.7,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:02+00:00",
      "request_id": "162b5a5a1974",
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
      "timestamp": "2026-11-10T09:10:02+00:00",
      "request_id": "e2ae0aff26cf",
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
      "duration_ms": 0.7,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:02+00:00",
      "request_id": "9dd29e11ecb5",
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
      "duration_ms": 1.0,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:02+00:00",
      "request_id": "47dd8db043ce",
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
      "timestamp": "2026-11-10T09:10:02+00:00",
      "request_id": "a74eb10ade75",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 301,
      "text_hash": "566a00236ffa",
      "status_code": 200,
      "outcome": "decided",
      "reason": null,
      "content_id": "825bf9437b1d",
      "guess": "unsure",
      "confidence": 0.532,
      "model_score": 0.5016,
      "style_score": 0.5624,
      "duration_ms": 69.7,
      "cpu_ms": 1031.2,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:02+00:00",
      "request_id": "7b658eb0c906",
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
      "timestamp": "2026-11-10T09:10:37+00:00",
      "request_id": "5da813e46c39",
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
      "duration_ms": 1.0,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:37+00:00",
      "request_id": "37f0945b94f7",
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
      "duration_ms": 0.7,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:37+00:00",
      "request_id": "1d744e31b499",
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
      "timestamp": "2026-11-10T09:10:37+00:00",
      "request_id": "d7d5c750c493",
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
      "duration_ms": 0.7,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:37+00:00",
      "request_id": "e5e60462d184",
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
      "duration_ms": 1.0,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:37+00:00",
      "request_id": "46d7cf42a9f1",
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
      "duration_ms": 0.8,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:38+00:00",
      "request_id": "4dad51663ef2",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 301,
      "text_hash": "566a00236ffa",
      "status_code": 200,
      "outcome": "decided",
      "reason": null,
      "content_id": "57dafa4fc6d1",
      "guess": "unsure",
      "confidence": 0.532,
      "model_score": 0.5016,
      "style_score": 0.5624,
      "duration_ms": 72.8,
      "cpu_ms": 1218.8,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:10:38+00:00",
      "request_id": "aa48c8c752e5",
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
      "duration_ms": 1.1,
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
      "timestamp": "2026-11-10T09:11:14+00:00",
      "request_id": "97c1f8ac915b",
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
      "duration_ms": 1.2,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:11:14+00:00",
      "request_id": "5daef88cf72e",
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
      "duration_ms": 0.8,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:11:14+00:00",
      "request_id": "d22af47ecfdc",
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
      "duration_ms": 0.8,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:11:14+00:00",
      "request_id": "80eb9504e673",
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
      "duration_ms": 1.1,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:11:14+00:00",
      "request_id": "e931eba373b9",
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
      "duration_ms": 1.0,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:11:14+00:00",
      "request_id": "169fff2efe8d",
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
      "duration_ms": 1.2,
      "cpu_ms": 0.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:11:14+00:00",
      "request_id": "a304eae1d086",
      "route": "/submit",
      "creator_id": "c1_flood",
      "text_type": "str",
      "text_chars": 301,
      "text_hash": "566a00236ffa",
      "status_code": 200,
      "outcome": "decided",
      "reason": null,
      "content_id": "54a91feafe09",
      "guess": "unsure",
      "confidence": 0.532,
      "model_score": 0.5016,
      "style_score": 0.5624,
      "duration_ms": 67.6,
      "cpu_ms": 1000.0,
      "detector_cold": false
    },
    {
      "timestamp": "2026-11-10T09:11:14+00:00",
      "request_id": "5ca925715871",
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
      "duration_ms": 1.3,
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

**Trial 2** (`run_capstone.py::crit2`)

```json
{
  "starts": [
    {
      "start": 1,
      "ready_s": 0.51,
      "first_submit_s": 3.53,
      "status": 200
    },
    {
      "start": 2,
      "ready_s": 0.51,
      "first_submit_s": 3.44,
      "status": 200
    },
    {
      "start": 3,
      "ready_s": 0.51,
      "first_submit_s": 3.5,
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
      "ready_s": 0.51,
      "first_submit_s": 3.66,
      "status": 200
    },
    {
      "start": 2,
      "ready_s": 0.52,
      "first_submit_s": 3.73,
      "status": 200
    },
    {
      "start": 3,
      "ready_s": 0.51,
      "first_submit_s": 3.47,
      "status": 200
    }
  ]
}
```

### Criterion 3 — Warm p95 ≤ 0.5 s, none > 1.5 s

**Trial 1** (`run_capstone.py::crit3`)

```json
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

**Trial 2** (`run_capstone.py::crit3`)

```json
{
  "p95_s": 0.263,
  "max_s": 0.271,
  "median_s": 0.172,
  "mean_s_by_words": {
    "100": 0.092,
    "250": 0.191,
    "600": 0.258
  },
  "all_200": true
}
```

**Trial 3** (`run_capstone.py::crit3`)

```json
{
  "p95_s": 0.357,
  "max_s": 0.476,
  "median_s": 0.193,
  "mean_s_by_words": {
    "100": 0.104,
    "250": 0.209,
    "600": 0.322
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
  ],
  "sample_records": [
    {
      "timestamp": "2026-11-10T09:10:27+00:00",
      "request_id": "5225c341ea60",
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
      "duration_ms": 2672.5,
      "cpu_ms": 2625.0,
      "detector_cold": true
    },
    {
      "timestamp": "2026-11-10T09:10:27+00:00",
      "request_id": "67b0563c751c",
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
      "duration_ms": 1.1,
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
    2667,
    13,
    2,
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
      "timestamp": "2026-11-10T09:11:03+00:00",
      "request_id": "167e643118e2",
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
      "duration_ms": 2661.7,
      "cpu_ms": 2578.1,
      "detector_cold": true
    },
    {
      "timestamp": "2026-11-10T09:11:03+00:00",
      "request_id": "dc4ff7012828",
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
      "duration_ms": 1.2,
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
    2532,
    13,
    12,
    11,
    12
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
      "timestamp": "2026-11-10T09:11:40+00:00",
      "request_id": "2950d0da461a",
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
      "duration_ms": 2527.3,
      "cpu_ms": 2531.2,
      "detector_cold": true
    },
    {
      "timestamp": "2026-11-10T09:11:40+00:00",
      "request_id": "84c125addf7b",
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
      "duration_ms": 1.1,
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
    "seconds": 0.11,
    "scores": [
      0.3753,
      0.6293,
      0.5023
    ],
    "ok": true
  },
  "one 3000-char word": {
    "status": 200,
    "seconds": 0.2,
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
    "seconds": 0.09,
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
    "seconds": 0.13,
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
    "seconds": 0.12,
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
    "seconds": 0.16,
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
    "seconds": 0.19,
    "scores": [
      0.997,
      0.725,
      0.861
    ],
    "ok": true
  },
  "newlines and tabs": {
    "status": 200,
    "seconds": 0.19,
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
    "seconds": 0.1,
    "scores": [
      0.3753,
      0.6293,
      0.5023
    ],
    "ok": true
  },
  "one 3000-char word": {
    "status": 200,
    "seconds": 0.22,
    "scores": [
      0.997,
      0.575,
      0.643
    ],
    "ok": true
  },
  "60 emoji": {
    "status": 200,
    "seconds": 0.12,
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
