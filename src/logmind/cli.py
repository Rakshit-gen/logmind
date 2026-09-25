import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="logmind")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_p = sub.add_parser("ingest-postmortems", help="ingest the postmortem library")
    ingest_p.add_argument("--input", required=True)

    analyze_p = sub.add_parser("analyze", help="analyze a log file for an active incident")
    analyze_p.add_argument("--logs", required=True)
    analyze_p.add_argument("--incident", required=True, help="plain language description")
    analyze_p.add_argument("--top-n", type=int, default=5, help="how many error signatures to rank")

    args = parser.parse_args()

    if args.command == "ingest-postmortems":
        from logmind.ingest_postmortems import ingest_postmortems

        count = ingest_postmortems(args.input)
        print(f"ingested {count} chunks from {args.input}")

    elif args.command == "analyze":
        from logmind.graph import run

        try:
            result = run(args.incident, args.logs, top_n=args.top_n)
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

        if result.get("clarifying_question"):
            print(result["clarifying_question"])
        else:
            print(result["report"])


if __name__ == "__main__":
    main()
