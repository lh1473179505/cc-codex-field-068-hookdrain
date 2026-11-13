from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from hookdrain.core import HookDrain


def _post(base, event):
    url = base.rstrip("/") + "/hook"
    body = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            resp.read()
    except Exception:
        pass


def run_replay(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ckpt = Path(args.checkpoint)

    core = HookDrain()
    if ckpt.is_file():
        core = HookDrain.from_state(json.loads(ckpt.read_text()))
    start = core.arrival_index

    lines = [
        line
        for line in Path(args.events).read_text().splitlines()
        if line.strip()
    ]
    for index, line in enumerate(lines, start=1):
        if index <= start:
            continue
        event = json.loads(line)
        _post(args.base, event)
        core.apply(event, arrival_index=index)
        ckpt.write_text(json.dumps(core.to_state(), indent=2))

    orders = core.sorted_orders()
    (out / "orders.json").write_text(json.dumps(orders, indent=2) + "\n")
    late_text = "".join(json.dumps(row) + "\n" for row in core.late)
    (out / "late_arrivals.jsonl").write_text(late_text)
    (out / "watermark.json").write_text(
        json.dumps(core.watermark(), indent=2) + "\n"
    )
    print(
        f"replayed {len(lines)} events (resumed at {start + 1}), "
        f"unique_applied={core.unique_applied}, late={len(core.late)}"
    )
    return 0
