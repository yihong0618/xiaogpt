# xiaogpt

[![PyPI](https://img.shields.io/pypi/v/xiaogpt?style=flat-square)](https://pypi.org/project/xiaogpt)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/yihong0618/xiaogpt?color=%23086DCD&label=docker%20image)](https://hub.docker.com/r/yihong0618/xiaogpt)


https://user-images.githubusercontent.com/15976103/226803357-72f87a41-a15b-409e-94f5-e2d262eecd53.mp4


Play ChatGPT and other LLM with Xiaomi AI Speaker

![image](https://user-images.githubusercontent.com/15976103/220028375-c193a859-48a1-4270-95b6-ef540e54a621.png)
![image](https://user-images.githubusercontent.com/15976103/226802344-9c71f543-b73c-4a47-8703-4c200c434dec.png)

## 支持的 AI 类型

- GPT3
- ChatGPT
- New Bing
- [ChatGLM](http://open.bigmodel.cn/)
- [Bard](https://github.com/dsdanielpark/Bard-API)

## Windows 获取小米音响DID

1. `pip install miservice_fork`
2. `set MI_USER=xxxx`
3. `set MI_PASS=xxx`
4. 得到did
5. `set MI_DID=xxxx`
6. 具体可参考 `one_click.bat` 脚本
- 如果获取did报错时，请更换一下无线网络，有很大概率解决问题。

## 一点原理

[不用 root 使用小爱同学和 ChatGPT 交互折腾记](https://github.com/yihong0618/gitblog/issues/258)

## 准备

1. ChatGPT id
2. 小爱音响
3. 能正常联网的环境或 proxy
4. python3.8+

## 使用

- `pip install -U --force-reinstall xiaogpt`
- 参考我 fork 的 [MiService](https://github.com/yihong0618/MiService) 项目 README 并在本地 terminal 跑 `micli list` 拿到你音响的 DID 成功 **别忘了设置 export MI_DID=xxx** 这个 MI_DID 用
- run `xiaogpt --hardware ${your_hardware} --use_chatgpt_api` hardware 你看小爱屁股上有型号，输入进来，如果在屁股上找不到或者型号不对，可以用 `micli mina` 找到型号
- 跑起来之后就可以问小爱同学问题了，“帮我"开头的问题，会发送一份给 ChatGPT 然后小爱同学用 tts 回答
- 如果上面不可用，可以尝试用手机抓包，https://userprofile.mina.mi.com/device_profile/v2/conversation 找到 cookie 利用 `--cookie '${cookie}'` cookie 别忘了用单引号包裹
- 默认用目前 ubus, 如果你的设备不支持 ubus 可以使用 `--use_command` 来使用 command 来 tts
- 使用 `--mute_xiaoai` 选项，可以快速停掉小爱的回答
- 使用 `--account ${account} --password ${password}`
- 如果有能力可以自行替换唤醒词，也可以去掉唤醒词
- 使用 `--use_chatgpt_api` 的 api 那样可以更流畅的对话，速度特别快，达到了对话的体验, [openai api](https://platform.openai.com/account/api-keys), 命令 `--use_chatgpt_api`
- 使用 gpt-3 的 api 那样可以更流畅的对话，速度快, 请 google 如何用 [openai api](https://platform.openai.com/account/api-keys) 命令 --use_gpt3
- 如果你遇到了墙需要用 Cloudflare Workers 替换 api_base 请使用 `--api_base ${url}` 来替换。  **请注意，此处你输入的api应该是'`https://xxxx/v1`'的字样，域名需要用引号包裹**
- 可以跟小爱说 `开始持续对话` 自动进入持续对话状态，`结束持续对话` 结束持续对话状态。
- 可以使用 `--enable_edge_tts` 来获取更好的 tts 能力
- 可以使用 `--use_langchain` 替代 `--use_chatgpt_api` 来调用 LangChain（默认 chatgpt）服务，实现上网检索、数学运算..

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
# 使用流式响应，获得更快的响应
xiaogpt --hardware LX06  --mute_xiaoai --stream
# 如果你想使用 gpt3 ai
export OPENAI_API_KEY=${your_api_key}
xiaogpt --hardware LX06  --mute_xiaoai --use_gpt3
# 如果你想用 edge-tts
xiaogpt --hardware LX06 --cookie ${cookie} --use_chatgpt_api --enable_edge_tts
# 如果你想使用 LangChain + SerpApi 实现上网检索或其他本地服务（目前仅支持 stream 模式）
export OPENAI_API_KEY=${your_api_key}
export SERPAPI_API_KEY=${your_serpapi_key}
xiaogpt --hardware Lx06 --use_langchain --mute_xiaoai --stream --openai_key ${your_api_key} --serpapi_api_key ${your_serpapi_key}
```
使用 git clone 运行

```shell
export OPENAI_API_KEY=${your_api_key}
python3 xiaogpt.py --hardware LX06
# or
python3 xiaogpt.py --hardware LX06 --cookie ${cookie}
# 如果你想直接输入账号密码
python3 xiaogpt.py --hardware LX06 --account ${your_xiaomi_account} --password ${your_password} --use_chatgpt_api
# 如果你想 mute 小米的回答
python3 xiaogpt.py --hardware LX06  --mute_xiaoai
# 使用流式响应，获得更快的响应
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --stream
# 如果你想使用 gpt3 ai
export OPENAI_API_KEY=${your_api_key}
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_gpt3
# 如果你想使用 ChatGLM api
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_glm --glm_key ${glm_key}
# 如果你想使用 google 的 bard
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_bard --bard_token ${bard_token}
# 如果你想使用 LangChain+SerpApi 实现上网检索或其他本地服务（目前仅支持 stream 模式）
export OPENAI_API_KEY=${your_api_key}
export SERPAPI_API_KEY=${your_serpapi_key}
python3 xiaogpt.py --hardware Lx06 --use_langchain --mute_xiaoai --stream --openai_key ${your_api_key} --serpapi_api_key ${your_serpapi_key}
```

## config.json
如果想通过单一配置文件启动也是可以的, 可以通过 `--config` 参数指定配置文件, config 文件必须是合法的 JSON 格式
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

若要指定 OpenAI 的模型参数，如 model, temporature, top_p, 请在config.json中指定：

```json
{
    ...
    "gpt_options": {
        "temperature": 0.9,
        "top_p": 0.9,
    }
}
```

具体参数作用请参考 [Open AI API 文档](https://platform.openai.com/docs/api-reference/chat/create)。
ChatGLM [文档](http://open.bigmodel.cn/doc/api#chatglm_130b)
Bard-API [参考](https://github.com/dsdanielpark/Bard-API)
## 配置项说明

| 参数                  | 说明                                              | 默认值                              |
| --------------------- | ------------------------------------------------- | ----------------------------------- |
| hardware              | 设备型号                                          |                                     |
| account               | 小爱账户                                          |                                     |
| password              | 小爱账户密码                                      |                                     |
| openai_key            | openai的apikey                                    |                                     |
| serpapi_api_key            | serpapi的key  参考 [SerpAPI](https://serpapi.com/)                                  |                                     |
| glm_key               | chatglm 的 apikey                                    |                                     |
| bard_token            | bard 的 token 参考 [Bard-API](https://github.com/dsdanielpark/Bard-API)                                 |                                     |
| cookie                | 小爱账户cookie （如果用上面密码登录可以不填）     |                                     |
| mi_did                | 设备did                                           |                                     |
| use_command           | 使用 MI command 与小爱交互                        | `false`                             |
| mute_xiaoai           | 快速停掉小爱自己的回答                            | `true`                              |
| verbose               | 是否打印详细日志                                  | `false`                             |
| bot                   | 使用的 bot 类型，目前支持gpt3,chatgptapi和newbing | `chatgptapi`                        |
| enable_edge_tts       | 使用Edge TTS                                      | `false`                             |
| edge_tts_voice        | Edge TTS 的嗓音                                   | `zh-CN-XiaoxiaoNeural`              |
| prompt                | 自定义prompt                                      | `请用100字以内回答`                 |
| keyword               | 自定义请求词列表                                  | `["请问"]`                          |
| change_prompt_keyword | 更改提示词触发列表                                | `["更改提示词"]`                    |
| start_conversation    | 开始持续对话关键词                                | `开始持续对话`                      |
| end_conversation      | 结束持续对话关键词                                | `结束持续对话`                      |
| stream                | 使用流式响应，获得更快的响应                      | `false`                             |
| proxy                 | 支持 HTTP 代理，传入 http proxy URL               | ""                                  |
| gpt_options           | OpenAI API 的参数字典                             | `{}`                                |
| bing_cookie_path      | NewBing使用的cookie路径，参考[这里]获取           | 也可通过环境变量 `COOKIE_FILE` 设置 |
| bing_cookies          | NewBing使用的cookie字典，参考[这里]获取           |                                     |
| deployment_id         | Azure OpenAI 服务的 deployment ID                 |                                     |
| localhost             | 是否通过本地服务器加载EdgeTTS的音频输出           | `true`                              |

[这里]: https://github.com/acheong08/EdgeGPT#getting-authentication-required

## 注意

1. 请开启小爱同学的蓝牙
2. 如果要更改提示词和 PROMPT 在代码最上面自行更改
3. 目前已知 LX04、X10A 和 L05B L05C 可能需要使用 `--use_command`，否则可能会出现终端能输出GPT的回复但小爱同学不回答GPT的情况
4. 在wsl使用时, 需要设置代理为 http://wls的ip:port(vpn的代理端口), 否则会出现连接超时的情况, 详情 [报错： Error communicating with OpenAI](https://github.com/yihong0618/xiaogpt/issues/235)

## QA

1. 用破解么？不用
2. 你做这玩意也没用啊？确实。。。但是挺好玩的，有用对你来说没用，对我们来说不一定呀
3. 想把它变得更好？PR Issue always welcome.
4. 还有问题？提 Issue 哈哈

## 视频教程
https://www.youtube.com/watch?v=K4YA8YwzOOA

## Docker

### 常规用法
X86/ARM Docker Image: `yihong0618/xiaogpt`

```shell
docker run -e OPENAI_API_KEY=<your-openapi-key> yihong0618/xiaogpt <命令行参数>
```

如

```shell
docker run -e OPENAI_API_KEY=<your-openapi-key> yihong0618/xiaogpt --account=<your-xiaomi-account> --password=<your-xiaomi-password> --hardware=<your-xiaomi-hardware> --use_chatgpt_api
```

### 使用配置文件
xiaogpt的配置文件可通过指定volume /config，以及指定参数--config来处理，如
```shell
docker run -v <your-config-dir>:/config yihong0618/xiaogpt --config=/config/config.json
```

### 本地编译Docker Image
```shell
 docker build -t xiaogpt .
```
如果需要在Apple M1/M2上编译x86
```shell
 docker buildx build --platform=linux/amd64 -t xiaogpt-x86 .
```

### Add edge-tts
edge-tts提供了类似微软tts的能力
- https://github.com/rany2/edge-tts

#### Usage
你可以通过参数`enable_edge_tts`, 来启用它
```json
{
  "enable_edge_tts": true,
  "edge_tts_voice": "zh-CN-XiaoxiaoNeural"
}
```

查看更多语言支持, 从中选择一个
```shell
edge-tts --list-voices
```

#### 在容器中使用edge-tts

由于 Edge TTS 启动了一个本地的 HTTP 服务，所以需要将容器的端口映射到宿主机上，并且指定本地机器的 hostname:

```shell
docker run -v <your-config-dir>:/config yihong0618/xiaogpt -p 9527:9527 -e XIAOGPT_HOSTNAME=<your ip> --config=/config/config.json
```

注意端口必须映射为与容器内一致，XIAOGPT_HOSTNAME 需要设置为宿主机的 IP 地址，否则小爱无法正常播放语音。

如果不想使用本地的HTTP服务器，可以将配置中的 `localhost` 设置为 `false`，这样 Edge TTS 会通过一个网络上的三方服务器加载输出音频文件，但是这样会导致响应速度变慢。

## 推荐的 fork

- [MIGPT](https://github.com/Afool4U/MIGPT) -> 基于 API 流式对话的低延迟版MIGPT
- [XiaoBot](https://github.com/longbai/xiaobot) -> Go语言版本的Fork, 带支持不同平台的UI

## 感谢

- [xiaomi](https://www.mi.com/)
- [PDM](https://pdm.fming.dev/latest/)
- @[Yonsm](https://github.com/Yonsm) 的 [MiService](https://github.com/Yonsm/MiService)
- @[pjq](https://github.com/pjq) 给了这个项目非常多的帮助
- @[frostming](https://github.com/frostming) 重构了一些代码，支持了`持续会话功能`

## 赞赏

谢谢就够了
