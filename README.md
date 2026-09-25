# logmind

When something breaks in production, the first twenty minutes usually go
to grepping through logs across five services trying to figure out what
even changed, and nobody remembers that the exact same failure happened
four months ago and how it got fixed.

logmind splits that problem in two. A Spark job scans the raw log files
(these get large fast, one bad deploy can produce gigabytes of noise in
an hour) and pulls out which services and error signatures actually spiked
in the incident window. A LangGraph agent then takes that signal plus your
plain-language description of what's happening, checks it against a small
library of past incident postmortems, and writes up a short report: likely
cause, what changed, which past incidents look similar, and what to try
next.

## Why Spark for the logs but not for the postmortems

The log volume during an incident is the part that doesn't fit on one
thread, hundreds of thousands of lines across services. The postmortem
library, by contrast, is small on purpose, a few dozen documents written
by humans after incidents get resolved, so a plain ingestion pass is fine
there. Using Spark for both would be using a hammer because you already
have it out.

## Setup

Use Python 3.11 (PySpark's cloudpickle does not work correctly on 3.13+).

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
# add your GROQ_API_KEY to .env
```

## Usage

```bash
# generate some synthetic logs to try it out on, or point at your own
python -m logmind.log_generator --out sample_logs/incident.jsonl

# ingest the sample postmortems once
python -m logmind.cli ingest-postmortems --input postmortems

# run the agent against an incident
python -m logmind.cli analyze --logs sample_logs/incident.jsonl \
  --incident "checkout API returning 500s since 14:30, started right after the release"
```

## What a run looks like

Given the sample incident log (a synthetic checkout-api error spike) and
the sample postmortems, `analyze` finds the matching past incident and
writes something like:

```
Likely cause: checkout-api is failing because calls to payments-api are
erroring out (connection issues), matching a past incident from March
where a payments-api deploy shrank its connection pool.

Affected service: checkout-api, secondary: payments-api

Similar past incident: 2026-03-14 checkout-api 500s from payments-api
timeout, root cause was a connection pool misconfiguration, fixed by
reverting the pool size and adding a saturation alert.

Next steps:
1. Check whether payments-api had a recent deploy, especially to
   connection pool or timeout config.
2. Check payments-api connection pool saturation.
3. If this matches the March incident, the fix was reverting the pool
   size change, not a checkout-api change.
```

## Troubleshooting

**`PicklingError` on `createDataFrame` or `spark.read.json`**: you're on
Python 3.13+, PySpark's cloudpickle doesn't handle it. Use 3.11.

**`ModuleNotFoundError: No module named 'logmind'` from a spark task**:
run `pip install -e .`, spark workers import your code by name and don't
share the driver's `sys.path`.

## Production considerations

What's handled:

- **Docker**: a `Dockerfile` builds an image with Python 3.11 and a JDK
  (via `default-jdk-headless`) so pyspark has a JVM to run on. Runs the
  `analyze` and `ingest-postmortems` CLI commands. `GROQ_API_KEY` is
  passed in at container run time, not baked into the image.
- **CI**: `.github/workflows/ci.yml` runs on every push and pull request,
  sets up Python 3.11 and JDK 17, installs the package, and runs the test
  suite.
- **Structured logging**: `cli.py` logs status (what's being analyzed,
  errors, whether a report or a clarifying question came back) through
  Python's `logging` module instead of scattered `print` calls. The
  actual report or clarifying question still goes to stdout, since
  that's the tool's real output and needs to stay pipeable.
- **Retries**: the Groq call in `synthesize_report_node` retries up to 3
  times with exponential backoff for transient failures (rate limits,
  timeouts). A missing or invalid API key still fails immediately, it's
  checked before the retry logic ever runs.
- **Input validation**: pointing `--logs` at a file that doesn't exist
  gives a clear error instead of a raw Spark stack trace.

What a real production deployment would still need:

- **A real Spark cluster.** This runs `local[2]`, capped on purpose for
  a laptop. Real incident log volumes across many services would need
  actual distributed Spark (YARN, Kubernetes, or a managed service like
  EMR/Dataproc), not a single JVM process.
- **Auth.** There is none. Anyone who can run the CLI or hit whatever
  wraps it can trigger analysis and read the postmortem library. A real
  deployment needs this behind some access control, especially since
  postmortems can contain sensitive operational detail.
- **Automated postmortem ingestion.** `ingest-postmortems` is a manual
  step you run by hand after writing a postmortem. In practice you'd
  want this triggered automatically, e.g. a hook when a postmortem doc
  is merged, so the library never silently drifts out of date.
- **Secrets management.** `GROQ_API_KEY` comes from a `.env` file or an
  environment variable. That's fine for local use, but production wants
  a real secrets manager rather than an env var sitting on a host.
- **Observability beyond logs.** The logging added here is a starting
  point, not tracing or metrics. There's no visibility into Groq latency,
  retry counts, or how often the agent asks a clarifying question versus
  synthesizing a report, which matters if this is trusted during actual
  incidents.
- **Persistent, shared Chroma storage.** `CHROMA_DIR` is a local
  directory. Multiple instances of this tool running in production would
  each need to read the same postmortem index, which means a shared
  store, not a directory on one machine's disk.
- **Rate limiting and cost control on the Groq calls.** Nothing here
  stops repeated or abusive calls from running up API usage.

## Layout

```
src/logmind/
  config.py            env vars and constants
  spark_session.py     capped local spark session
  log_generator.py     synthetic log data for trying this out without real logs
  log_analysis.py      spark job that finds error spikes by service
  store.py             chroma wrapper for the postmortem library
  ingest_postmortems.py
  graph.py             the langgraph agent
  cli.py               analyze / ingest-postmortems commands
```
