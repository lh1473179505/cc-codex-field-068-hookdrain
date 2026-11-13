import argparse
def main(argv=None):
    p=argparse.ArgumentParser(prog="hookdrain")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("site")
    s.add_argument("--port", type=int, default=8768)
    s.add_argument("--host", default="127.0.0.1")
    r=sub.add_parser("replay")
    r.add_argument("--base", required=True)
    r.add_argument("--events", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--checkpoint", required=True)
    v=sub.add_parser("verify")
    v.add_argument("--out", required=True)
    v.add_argument("--expect", required=True)
    args=p.parse_args(argv)
    if args.cmd=="site":
        from hookdrain.site import serve
        serve(args.host, args.port); return 0
    if args.cmd=="replay":
        from hookdrain.replay import run_replay
        return run_replay(args)
    if args.cmd=="verify":
        from hookdrain.verify import run_verify
        return run_verify(args)
    return 2
if __name__=="__main__":
    raise SystemExit(main())
