FROM python:3.10 AS builder
WORKDIR /app
COPY requirements.txt .
# 设置默认的源地址为 PyPI 官方源
ARG PIP_INDEX_URL=https://pypi.org/simple
# 使用 ARG 定义的变量作为 pip 源地址
RUN python3 -m venv .venv && .venv/bin/pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX_URL}

FROM python:3.10-slim

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
