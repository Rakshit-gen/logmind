FROM python:3.11-slim

# pyspark needs a JVM. default-jdk-headless pulls in openjdk 17 on
# debian bookworm (the base for python:3.11-slim) and satisfies pyspark
# 3.5's Java 17+ requirement. It also sets up the /usr/lib/jvm/default-java
# symlink (via the java-common package) so JAVA_HOME doesn't have to
# hardcode an architecture-specific path like java-17-openjdk-amd64.
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

# spark defaults to local[2] (src/logmind/spark_session.py), fine for a
# single container. GROQ_API_KEY must be supplied at runtime, it is not
# baked into the image.
ENTRYPOINT ["python", "-m", "logmind.cli"]
CMD ["--help"]
