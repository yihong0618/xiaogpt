FROM python:3.12 AS builder
WORKDIR /app
COPY pyproject.toml pdm.lock* ./
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install pdm && \
    python3 -m venv .venv && \
    .venv/bin/pdm install --prod --no-editable -G :all --config install.pypi_url=${PIP_INDEX_URL}

FROM python:3.12

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY xiaogpt/ ./xiaogpt/
COPY xiaogpt.py .
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV XDG_CONFIG_HOME=/config
ENV XIAOGPT_PORT=9527
VOLUME /config
EXPOSE 9527
ENTRYPOINT ["/app/.venv/bin/python3", "xiaogpt.py"]
