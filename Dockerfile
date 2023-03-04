FROM python:3
WORKDIR /app
RUN pip install aiohttp
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV OPENAI_API_KEY=<your-api-key>
VOLUME /config
ENTRYPOINT ["python3","xiaogpt.py"]