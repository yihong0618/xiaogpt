FROM python:3.10
WORKDIR /app
RUN pip install aiohttp
# Install Rust using rustup
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
# Add Rust to the PATH
ENV PATH="/root/.cargo/bin:${PATH}"
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV XDG_CONFIG_HOME=/config
VOLUME /config
ENTRYPOINT ["python3","xiaogpt.py"]