# xiaogpt
Play ChatGPT with Xiaomi AI Speaker

![image](https://user-images.githubusercontent.com/15976103/220028375-c193a859-48a1-4270-95b6-ef540e54a621.png)


## 一点原理

[不用 root 使用小爱同学和 ChatGPT 交互折腾记](https://github.com/yihong0618/gitblog/issues/258)


## 准备

1. ChatGPT id
2. 小爱音响
3. 能正常联网的环境或 proxy
4. python3.8+

## 使用

- pip install -U xiaogpt 
- 参考我 fork 的 [MiService](https://github.com/yihong0618/MiService) 项目 README 并在本地 terminal 跑 `micli list` 拿到你音响的 DID 成功 **别忘了设置 export MI_DID=xxx** 这个 MI_DID 用 
- run `python xiaogpt.py --hardware ${your_hardware}` hardware 你看小爱屁股上有型号，输入进来
- 跑起来之后就可以问小爱同学问题了，“帮我"开头的问题，会发送一份给 ChatGPT 然后小爱同学用 tts 回答
- 如果上面不可用，可以尝试用手机抓包，https://userprofile.mina.mi.com/device_profile/v2/conversation 找到 cookie 利用 --cookie '${cookie}' cookie 别忘了用单引号包裹
- 默认用目前 ubus, 如果你的设备不支持 ubus 可以使用 --use_command 来使用 command 来 tts
- 使用 --mute_xiaoai 选项，可以快速停掉小爱的回答
- 使用 --account ${account} --password ${password}
- 如果有能力可以自行替换唤醒词，也可以去掉唤醒词
- 使用 --use_chatgpt_api 的 api 那样可以更流畅的对话，速度特别快，达到了对话的体验, [openai api](https://platform.openai.com/account/api-keys), 命令 --use_chatgpt_api
- 使用 gpt-3 的 api 那样可以更流畅的对话，速度快, 请 google 如何用 [openai api](https://platform.openai.com/account/api-keys) 命令 --use_gpt3
- 如果你遇到了墙需要用 Cloudflare Workers 替换 api_base 请使用 `--api_base ${url}` 来替换。  **请注意，此处你输入的api应该是'`https://xxxx/v1`'的字样，域名需要用引号包裹**
- 可以跟小爱说 `开始持续对话` 自动进入持续对话状态，`结束持续对话` 结束持续对话状态。

e.g.

```shell
export OPENAI_API_KEY=${your_api_key}
xiaogpt --hardware LX06 --use_chatgpt_api 
# or 
xiaogpt --hardware LX06 --cookie ${cookie} --use_chatgpt_api
# 如果你想直接输入账号密码
xiaogpt --hardware LX06 --account ${your_xiaomi_account} --password ${your_password} --use_chatgpt_api
# 如果你想 mute 小米的回答
xiaogpt --hardware LX06  --mute_xiaoai --use_chatgpt_api
# 如果你想使用 gpt3 ai
export OPENAI_API_KEY=${your_api_key}
xiaogpt --hardware LX06  --mute_xiaoai --use_gpt3
```
使用 git clone 运行

```shell
export OPENAI_API_KEY=${your_api_key}
python3 xiaogpt.py --hardware LX06 --use_chatgpt_api
# or
python3 xiaogpt.py --hardware LX06 --cookie ${cookie} --use_chatgpt_api
# 如果你想直接输入账号密码
python3 xiaogpt.py --hardware LX06 --account ${your_xiaomi_account} --password ${your_password} --use_chatgpt_api
# 如果你想 mute 小米的回答
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_chatgpt_api
# 如果你想使用 gpt3 ai
export OPENAI_API_KEY=${your_api_key}
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_gpt3
```

## config.json
如果想通过单一配置文件启动也是可以的, 可以通过 --config 参数指定配置文件, config 文件必须是合法的 JSON 格式
参数优先级
- cli args > default > config

```shell
python3 xiaogpt.py --config xiao_config.json
# or
xiaogpt --config xiao_config.json
```
或者
```shell
cp xiao_config.json.example xiao_config.json
python3 xiaogpt.py 
```

## 注意

1. 请开启小爱同学的蓝牙
2. 如果要更改提示词和 PROMPT 在代码最上面自行更改
3. 目前已知 LX04 和 L05B L05C 可能需要使用 `--use_command`

## QA

1. 用破解么？不用
2. 你做这玩意也没用啊？确实。。。但是挺好玩的，有用对你来说没用，对我们来说不一定呀
3. 想把它变得更好？PR Issue always welcome.
4. 还有问题？提 Issuse 哈哈

## 视频教程
https://www.youtube.com/watch?v=K4YA8YwzOOA

## Docker

### 常规用法
X86/ARM Docker Image
- X86: pengjianqing/xiaogpt-x86
- ARM: pengjianqing/xiaogpt

docker run -e OPENAI_API_KEY=< your-openapi-key > pengjianqing/xiaogpt-x86 < 命令行参数 >

如

```shell
docker run -e OPENAI_API_KEY=<your-openapi-key> pengjianqing/xiaogpt-x86 --account=<your-xiaomi-account> --password=<your-xiaomi-password> --hardware=<your-xiaomi-hardware> --use_chatgpt_api
```

### 使用配置文件

1.xiaogpt的配置文件可通过指定volume /config，以及指定参数--config来处理，如

```shell
docker run -e OPENAI_API_KEY=<your-openapi-key> -v <your-config-dir>:/config pengjianqing/xiaogpt-x86 --account=<your-xiaomi-account> --password=<your-xiaomi-password> --hardware=<your-xiaomi-hardware> --use_chatgpt_api --config=/config/config.json
```

2.如果使用revChatGPT，则可通过指定volume /config，以及指定环境变量XDG_CONFIG_HOME来处理 ( **revChatGPT配置文件需要放置到<your-config-dir>/revChatGPT/config.json** ) ，如

```shell
docker run -e XDG_CONFIG_HOME=/config -v <your-config-dir>:/config pengjianqing/xiaogpt-x86 --account=<your-xiaomi-account> --password=<your-xiaomi-password> --hardware=<your-xiaomi-hardware> --use_chatgpt_api --config=/config/config.json
```

### 本地编译Docker Image
```shell
 docker build -t xiaogpt .
```
如果需要在Apple M1/M2上编译x86
```shell
 docker buildx build --platform=linux/amd64 -t xiaogpt-x86 .
```

## 推荐的 fork

- [MIGPT](https://github.com/Afool4U/MIGPT) -> 基于 API 流式对话的低延迟版MIGPT

## 感谢

- [xiaomi](https://www.mi.com/)
- @[Yonsm](https://github.com/Yonsm) 的 [MiService](https://github.com/Yonsm/MiService) 
- @[pjq](https://github.com/pjq) 给了这个项目非常多的帮助
- @[frostming](https://github.com/frostming) 重构了一些代码，支持了`持续会话功能`

## 赞赏

谢谢就够了
