"""
Start and stop the service as a child process — shared by `measure_cost.py` and
`run_capstone.py`, so every measurement starts the service the way RUNNING.md
tells a reader to (`python app.py`), not through a test client.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).parent


def start(port: int, log_dir: Path | None = None, extra_env: dict | None = None,
          out_path: Path | None = None) -> tuple[subprocess.Popen, float]:
    """Launch `python app.py`. Returns (process, launch_time_perf_counter)."""
    env = dict(os.environ, PORT=str(port), AI201_DEBUG="0", AI201_RATE_LIMITS="1")
    if log_dir is not None:
        env["AI201_LOG_DIR"] = str(log_dir)
    env.update(extra_env or {})
    out_path = Path(out_path) if out_path else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out = open(out_path, "ab") if out_path else subprocess.DEVNULL
    t0 = time.perf_counter()
    proc = subprocess.Popen([sys.executable, str(ROOT / "app.py")], cwd=ROOT,
                            env=env, stdout=out, stderr=subprocess.STDOUT)
    return proc, t0


def wait_ready(port: int, proc: subprocess.Popen, timeout: float = 180.0) -> float:
    """Block until /health answers; return seconds since this call began."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        if proc.poll() is not None:
            raise RuntimeError(f"service exited early with code {proc.returncode}")
        try:
            if requests.get(f"http://127.0.0.1:{port}/health", timeout=2).ok:
                return time.perf_counter() - t0
        except requests.RequestException:
            time.sleep(0.2)
    raise TimeoutError("service did not answer /health in time")


def stop(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
