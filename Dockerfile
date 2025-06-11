FROM python:3.12 AS builder
WORKDIR /app
COPY . .
RUN pip install pdm && \
    pdm install

FROM python:3.12

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .

ENV XDG_CONFIG_HOME=/config
ENV XIAOGPT_PORT=9527
VOLUME /config
EXPOSE 9527
ENTRYPOINT ["pdm", "run", "xiaogpt.py"]
