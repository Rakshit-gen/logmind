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

## Troubleshooting

**`PicklingError` on `createDataFrame` or `spark.read.json`**: you're on
Python 3.13+, PySpark's cloudpickle doesn't handle it. Use 3.11.

**`ModuleNotFoundError: No module named 'logmind'` from a spark task**:
run `pip install -e .`, spark workers import your code by name and don't
share the driver's `sys.path`.

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
