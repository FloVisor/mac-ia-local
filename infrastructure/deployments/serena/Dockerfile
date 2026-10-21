FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git nodejs npm && rm -rf /var/lib/apt/lists/*
COPY . /opt/serena
RUN pip install --no-cache-dir /opt/serena
ENV SERENA_HOME=/state/home
ENTRYPOINT ["serena", "start-mcp-server"]
