FROM python:3.10
WORKDIR /app
RUN pip install aiohttp
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV XDG_CONFIG_HOME=/config
VOLUME /config
ENTRYPOINT ["python3","xiaogpt.py"]