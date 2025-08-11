FROM python:3.12

WORKDIR /app

# 首先复制全部代码
COPY . .

# 直接安装依赖
RUN pip install --no-cache-dir -e .

ENV XDG_CONFIG_HOME=/config
ENV XIAOGPT_PORT=9527
VOLUME /config
EXPOSE 9527
ENTRYPOINT ["python", "xiaogpt.py"]
