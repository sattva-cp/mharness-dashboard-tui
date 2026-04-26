import json, os, socket, subprocess, time
from pathlib import Path

MH = Path.home() / "mharness"

def detect():
    for p in [8000, 8080, 5000, 3000]:
        try:
            with socket.create_connection(("127.0.0.1", p), 1.5):
                return p
        except:
            pass
    return None

P = detect()

def get_state():
    if P:
        try:
            import urllib.request
            return json.loads(
                urllib.request.urlopen(
                    f"http://127.0.0.1:{P}/api/v1/state", timeout=2
                ).read().decode()
            )
        except:
            pass

    v = MH / ".venv" / "bin" / "python"
    cmds = [[str(v), "-m", "mharness", "--json-status"]] if v.exists() else []
    cmds += [
        ["python3", "-m", "mharness", "--json-status"],
        ["python3", "-m", "mharness", "status", "--json"],
    ]
    for c in cmds:
        try:
            r = subprocess.run(c, cwd=MH, capture_output=True, text=True, timeout=8)
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
        except:
            pass

    for f in ["state.json", "swarm_state.json"]:
        p = MH / f
        if p.exists() and time.time() - p.stat().st_mtime < 120:
            try:
                return json.load(open(p))
            except:
                pass

    # Fallback mock data
    return {
        "agents": [
            {
                "id": f"agent_{i:02d}",
                "status": ["idle", "running", "paused"][i % 3],
                "model": ["gpt-4o", "claude", "mixtral"][i % 3],
                "last_cost": 0.001 * i,
                "last_latency_ms": 120 + i * 10,
            }
            for i in range(1, 27)
        ],
        "swarm_state": "mock",
        "total_cost_session": 0.33,
        "queue_depth": 2,
        "memory_snippet": "⚠ CORE UNREACHABLE — DEMO MODE",
    }