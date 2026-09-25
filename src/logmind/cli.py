import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("logmind.cli")


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

        logger.info("ingesting postmortems from %s", args.input)
        count = ingest_postmortems(args.input)
        logger.info("ingested %d chunks from %s", count, args.input)
        print(f"ingested {count} chunks from {args.input}")

    elif args.command == "analyze":
        from logmind.graph import run

        logger.info("analyzing %s for incident: %s", args.logs, args.incident)
        try:
            result = run(args.incident, args.logs, top_n=args.top_n)
        except FileNotFoundError as e:
            logger.error("log file not found: %s", args.logs)
            print(str(e), file=sys.stderr)
            sys.exit(1)
        except RuntimeError as e:
            logger.error("analysis failed: %s", e)
            print(str(e), file=sys.stderr)
            sys.exit(1)

        if result.get("clarifying_question"):
            logger.info("no anomalies found, asking clarifying question")
            print(result["clarifying_question"])
        else:
            logger.info("report synthesized")
            print(result["report"])


if __name__ == "__main__":
    main()
