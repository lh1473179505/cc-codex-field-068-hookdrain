from __future__ import annotations
import json
from pathlib import Path

def rows(path):
    p=Path(path)
    if not p.is_file():
        return []
    text=p.read_text().strip()
    if not text:
        return []
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(l) for l in text.splitlines() if l.strip()]

def run_verify(args) -> int:
    out=Path(args.out)
    exp=json.loads(Path(args.expect).read_text())
    orders=rows(out/"orders.json")
    if not orders:
        # also accept orders.jsonl
        orders=rows(out/"orders.jsonl")
    got={r["order_id"]: r for r in orders}
    errors=[]
    for e in exp["orders"]:
        g=got.get(e["order_id"])
        if not g:
            errors.append(f"missing {e['order_id']}")
            continue
        for k in ("status","total_cents"):
            if g.get(k)!=e[k]:
                errors.append(f"{e['order_id']} {k} {g.get(k)!r} != {e[k]!r}")
    late=rows(out/"late_arrivals.jsonl")
    reasons={}
    for r in late:
        reasons.setdefault(r.get("order_id"), set()).add(r.get("reason"))
    for oid, reason in exp.get("late_reasons", {}).items():
        if reason not in reasons.get(oid, set()):
            errors.append(f"late {oid} missing reason {reason} (have {reasons.get(oid)})")
    if errors:
        print("verify failed:")
        for e in errors:
            print(" -", e)
        return 1
    print("verify ok")
    return 0
