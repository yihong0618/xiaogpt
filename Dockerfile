FROM python:3.14

WORKDIR /app
COPY . .

RUN pip install pdm==2.29.2 && \
    pdm install --prod --no-self --frozen-lockfile

ENV XIAOGPT_MI_TOKEN_PATH=/config/.mi.token
ENV XDG_CONFIG_HOME=/config
ENV XIAOGPT_PORT=9527
VOLUME /config
EXPOSE 9527
ENTRYPOINT ["pdm", "run", "xiaogpt.py"]
