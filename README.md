# xiaogpt

[![PyPI](https://img.shields.io/pypi/v/xiaogpt?style=flat-square)](https://pypi.org/project/xiaogpt)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/yihong0618/xiaogpt?color=%23086DCD&label=docker%20image)](https://hub.docker.com/r/yihong0618/xiaogpt)

<https://user-images.githubusercontent.com/15976103/226803357-72f87a41-a15b-409e-94f5-e2d262eecd53.mp4>

Play ChatGPT and other LLM with Xiaomi AI Speaker

![image](https://user-images.githubusercontent.com/15976103/220028375-c193a859-48a1-4270-95b6-ef540e54a621.png)
![image](https://user-images.githubusercontent.com/15976103/226802344-9c71f543-b73c-4a47-8703-4c200c434dec.png)

## 支持的 AI 类型

- ChatGPT
- New Bing
- [ChatGLM](http://open.bigmodel.cn/)
- [Gemini](https://makersuite.google.com/app/apikey)
- [Doubao](https://console.volcengine.com/iam/keymanage/)
- [Moonshot](https://platform.moonshot.cn/docs/api/chat#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B)
- [01](https://platform.lingyiwanwu.com/apikeys)
- [Llama3](https://console.groq.com/docs/quickstart)
- [通义千问](https://help.aliyun.com/zh/dashscope/developer-reference/api-details)

## 获取小米音响DID

| 系统和Shell   | Linux *sh                                      | Windows CMD用户                        | Windows PowerShell用户                         |
| ------------- | ---------------------------------------------- | -------------------------------------- | ---------------------------------------------- |
| 1、安装包     | `pip install miservice_fork`                   | `pip install miservice_fork`           | `pip install miservice_fork`                   |
| 2、设置变量   | `export MI_USER=xxx` <br> `export MI_PASS=xxx` | `set MI_USER=xxx`<br>`set MI_PASS=xxx` | `$env:MI_USER="xxx"` <br> `$env:MI_PASS="xxx"` |
| 3、取得MI_DID | `micli list`                                   | `micli list`                           | `micli list`                                   |
| 4、设置MI_DID | `export MI_DID=xxx`                            | `set MI_DID=xxx`                       | `$env:MI_DID="xxx"`                            |

- 注意不同shell 对环境变量的处理是不同的，尤其是powershell赋值时，可能需要双引号来包括值。
- 如果获取did报错时，请更换一下无线网络，有很大概率解决问题。

## 一点原理

[不用 root 使用小爱同学和 ChatGPT 交互折腾记](https://github.com/yihong0618/gitblog/issues/258)

## 准备

1. ChatGPT id
2. 小爱音响
3. 能正常联网的环境或 proxy
4. python3.8+

## 使用

- `pip install -U --force-reinstall xiaogpt[locked]`
- 参考我 fork 的 [MiService](https://github.com/yihong0618/MiService) 项目 README 并在本地 terminal 跑 `micli list` 拿到你音响的 DID 成功 **别忘了设置 export MI_DID=xxx** 这个 MI_DID 用
- run `xiaogpt --hardware ${your_hardware} --use_chatgpt_api` hardware 你看小爱屁股上有型号，输入进来，如果在屁股上找不到或者型号不对，可以用 `micli mina` 找到型号
- 跑起来之后就可以问小爱同学问题了，“帮我"开头的问题，会发送一份给 ChatGPT 然后小爱同学用 tts 回答
- 如果上面不可用，可以尝试用手机抓包，<https://userprofile.mina.mi.com/device_profile/v2/conversation> 找到 cookie 利用 `--cookie '${cookie}'` cookie 别忘了用单引号包裹
- 默认用目前 ubus, 如果你的设备不支持 ubus 可以使用 `--use_command` 来使用 command 来 tts
- 使用 `--mute_xiaoai` 选项，可以快速停掉小爱的回答
- 使用 `--account ${account} --password ${password}`
- 如果有能力可以自行替换唤醒词，也可以去掉唤醒词
- 使用 `--use_chatgpt_api` 的 api 那样可以更流畅的对话，速度特别快，达到了对话的体验, [openai api](https://platform.openai.com/account/api-keys), 命令 `--use_chatgpt_api`
- 如果你遇到了墙需要用 Cloudflare Workers 替换 api_base 请使用 `--api_base ${url}` 来替换。 **请注意，此处你输入的api应该是'`https://xxxx/v1`'的字样，域名需要用引号包裹**
- `--use_moonshot_api` and other models please refer below
- 可以跟小爱说 `开始持续对话` 自动进入持续对话状态，`结束持续对话` 结束持续对话状态。
- 可以使用 `--tts edge` 来获取更好的 tts 能力
- 可以使用 `--tts openai` 来获取 openai tts 能力
- 可以使用 `--tts azure --azure_tts_speech_key <your-speech-key>` 来获取 Azure TTS 能力
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
# 如果你想使用 google 的 gemini
xiaogpt --hardware LX06  --mute_xiaoai --use_gemini --gemini_key ${gemini_key}
# 如果你想使用自己的 google gemini 服务
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_gemini --gemini_key ${gemini_key} --gemini_api_domain ${gemini_api_domain}
# 如果你想使用阿里的通义千问
xiaogpt --hardware LX06  --mute_xiaoai --use_qwen --qwen_key ${qwen_key}
# 如果你想使用 kimi
xiaogpt --hardware LX06  --mute_xiaoai --use_moonshot_api --moonshot_api_key ${moonshot_api_key}
# 如果你想使用 llama3
xiaogpt --hardware LX06  --mute_xiaoai --use_llama --llama_api_key ${llama_api_key}
# 如果你想使用 01
xiaogpt --hardware LX06  --mute_xiaoai --use_yi_api --ti_api_key ${yi_api_key}
# 如果你想使用豆包




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
# 如果你想使用 ChatGLM api
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_glm --glm_key ${glm_key}
# 如果你想使用 google 的 gemini
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_gemini --gemini_key ${gemini_key}
# 如果你想使用自己的 google gemini 服务
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_gemini --gemini_key ${gemini_key} --gemini_api_domain ${gemini_api_domain}
# 如果你想使用阿里的通义千问
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_qwen --qwen_key ${qwen_key}
# 如果你想使用 kimi
xiaogpt --hardware LX06  --mute_xiaoai --use_moonshot_api --moonshot_api_key ${moonshot_api_key}
# 如果你想使用 01
xiaogpt --hardware LX06  --mute_xiaoai --use_yi_api --ti_api_key ${yi_api_key}
# 如果你想使用豆包
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_doubao --stream --volc_access_key xxxx --volc_secret_key xxx
# 如果你想使用 llama3
python3 xiaogpt.py --hardware LX06  --mute_xiaoai --use_llama --llama_api_key ${llama_api_key}
# 如果你想使用 LangChain+SerpApi 实现上网检索或其他本地服务（目前仅支持 stream 模式）
export OPENAI_API_KEY=${your_api_key}
export SERPAPI_API_KEY=${your_serpapi_key}
python3 xiaogpt.py --hardware Lx06 --use_langchain --mute_xiaoai --stream --openai_key ${your_api_key} --serpapi_api_key ${your_serpapi_key}
```

## config.yaml

如果想通过单一配置文件启动也是可以的, 可以通过 `--config` 参数指定配置文件, config 文件必须是合法的 Yaml 或 JSON 格式
参数优先级

- cli args > default > config

```shell
python3 xiaogpt.py --config xiao_config.yaml
# or
xiaogpt --config xiao_config.yaml
```

或者

```shell
cp xiao_config.yaml.example xiao_config.yaml
python3 xiaogpt.py
```

若要指定 OpenAI 的模型参数，如 model, temporature, top_p, 请在 config.yaml 中指定：

```yaml
gpt_options:
  temperature: 0.9
  top_p: 0.9
```

具体参数作用请参考 [Open AI API 文档](https://platform.openai.com/docs/api-reference/chat/create)。
ChatGLM [文档](http://open.bigmodel.cn/doc/api#chatglm_130b)

## 配置项说明

| 参数                  | 说明                                                                                                       | 默认值                                                                                                    | 可选值                                                           |
| --------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| hardware              | 设备型号                                                                                                   |                                                                                                           |                                                                  |
| account               | 小爱账户                                                                                                   |                                                                                                           |                                                                  |
| password              | 小爱账户密码                                                                                               |                                                                                                           |                                                                  |
| openai_key            | openai的apikey                                                                                             |                                                                                                           |                                                                  |
| moonshot_api_key      | moonshot kimi 的 [apikey](https://platform.moonshot.cn/docs/api/chat#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B) |                                                                                                           |                                                                  |
| yi_api_key            | 01 wanwu 的 [apikey](https://platform.lingyiwanwu.com/apikeys)                                             |                                                                                                           |                                                                  |
| llama_api_key         | groq 的 llama3 [apikey](https://console.groq.com/docs/quickstart)                                          |                                                                                                           |                                                                  |
| serpapi_api_key       | serpapi的key 参考 [SerpAPI](https://serpapi.com/)                                                          |                                                                                                           |                                                                  |
| glm_key               | chatglm 的 apikey                                                                                          |                                                                                                           |                                                                  |
| gemini_key            | gemini 的 apikey [参考](https://makersuite.google.com/app/apikey)                                          |                                                                                                           |                                                                  |
| gemini_api_domain     | gemini 的自定义域名 [参考](https://github.com/antergone/palm-netlify-proxy)                                |                                                                                                           |
| qwen_key              | qwen 的 apikey [参考](https://help.aliyun.com/zh/dashscope/developer-reference/api-details)                |                                                                                                           |                                                                  |
| cookie                | 小爱账户cookie （如果用上面密码登录可以不填）                                                              |                                                                                                           |                                                                  |
| mi_did                | 设备did                                                                                                    |                                                                                                           |                                                                  |
| use_command           | 使用 MI command 与小爱交互                                                                                 | `false`                                                                                                   |                                                                  |
| mute_xiaoai           | 快速停掉小爱自己的回答                                                                                     | `true`                                                                                                    |                                                                  |
| verbose               | 是否打印详细日志                                                                                           | `false`                                                                                                   |                                                                  |
| bot                   | 使用的 bot 类型，目前支持 chatgptapi,newbing, qwen, gemini                                                 | `chatgptapi`                                                                                              |                                                                  |
| tts                   | 使用的 TTS 类型                                                                                            | `mi`                                                                                                      | `edge`、 `openai`、`azure`、`volc`、`baidu`、`google`、`minimax` |
| tts_options           | TTS 参数字典，参考 [tetos](https://github.com/frostming/tetos) 获取可用参数                                |                                                                                                           |                                                                  |
| prompt                | 自定义prompt                                                                                               | `请用100字以内回答`                                                                                       |                                                                  |
| keyword               | 自定义请求词列表                                                                                           | `["请"]`                                                                                                  |                                                                  |
| change_prompt_keyword | 更改提示词触发列表                                                                                         | `["更改提示词"]`                                                                                          |                                                                  |
| start_conversation    | 开始持续对话关键词                                                                                         | `开始持续对话`                                                                                            |                                                                  |
| end_conversation      | 结束持续对话关键词                                                                                         | `结束持续对话`                                                                                            |                                                                  |
| stream                | 使用流式响应，获得更快的响应                                                                               | `true`                                                                                                    |                                                                  |
| proxy                 | 支持 HTTP 代理，传入 http proxy URL                                                                        | ""                                                                                                        |                                                                  |
| gpt_options           | OpenAI API 的参数字典                                                                                      | `{}`                                                                                                      |                                                                  |
| deployment_id         | Azure OpenAI 服务的 deployment ID                                                                          | 参考这个[如何找到deployment_id](https://github.com/yihong0618/xiaogpt/issues/347#issuecomment-1784410784) |                                                                  |
| api_base              | 如果需要替换默认的api,或者使用Azure OpenAI 服务                                                            | 例如：`https://abc-def.openai.azure.com/`                                                                 |
| volc_access_key       | 火山引擎的 access key 请在[这里](https://console.volcengine.com/iam/keymanage/)获取                        |                                                                                                           |                                                                  |
| volc_secret_key       | 火山引擎的 secret key 请在[这里](https://console.volcengine.com/iam/keymanage/)获取                        |                                                                                                           |

## 注意

1. 请开启小爱同学的蓝牙
2. 如果要更改提示词和 PROMPT 在代码最上面自行更改
3. 目前已知 LX04、X10A 和 L05B L05C 可能需要使用 `--use_command`，否则可能会出现终端能输出GPT的回复但小爱同学不回答GPT的情况。这几个型号也只支持小爱原本的 tts.
4. 在wsl使用时, 需要设置代理为 <http://wls的ip:port(vpn的代理端口)>, 否则会出现连接超时的情况, 详情 [报错： Error communicating with OpenAI](https://github.com/yihong0618/xiaogpt/issues/235)

## QA

1. 用破解么？不用
2. 你做这玩意也没用啊？确实。。。但是挺好玩的，有用对你来说没用，对我们来说不一定呀
3. 想把它变得更好？PR Issue always welcome.
4. 还有问题？提 Issue 哈哈
5. Exception: Error <https://api2.mina.mi.com/admin/v2/device_list?master=0&requestId=app_ios_xxx>: Login failed [@KJZH001](https://github.com/KJZH001)<br>
   这是由于小米风控导致，海外地区无法登录大陆的账户，请尝试cookie登录
   无法抓包的可以在本地部署完毕项目后再用户文件夹`C:\Users\用户名`下面找到.mi.token，然后扔到你无法登录的服务器去<br>
   若是linux则请放到当前用户的home文件夹，此时你可以重新执行先前的命令，不出意外即可正常登录（但cookie可能会过一段时间失效，需要重新获取）<br>
   详情请见 [https://github.com/yihong0618/xiaogpt/issues/332](https://github.com/yihong0618/xiaogpt/issues/332)

## 视频教程

<https://www.youtube.com/watch?v=K4YA8YwzOOA>

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
docker run -v <your-config-dir>:/config yihong0618/xiaogpt --config=/config/config.yaml
```

### 网络使用 host 模型

```shell
docker run -v <your-config-dir>:/config --network=host yihong0618/xiaogpt --config=/config/config.yaml
```

### 本地编译Docker Image

```shell
 docker build -t xiaogpt .
```

如果在安装依赖时构建失败或安装缓慢时，可以在构建 Docker 镜像时使用 `--build-arg` 参数来指定国内源地址：

```sh
docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple -t xiaogpt .
```

如果需要在Apple M1/M2上编译x86

```shell
 docker buildx build --platform=linux/amd64 -t xiaogpt-x86 .
```

### 第三方 TTS

我们目前支持是三种第三方 TTS：edge/openai/azure/volc/baidu/google

[edge-tts](https://github.com/rany2/edge-tts) 提供了类似微软tts的能力
[azure-tts](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/9-more-realistic-ai-voices-for-conversations-now-generally/ba-p/4099471) 提供了微软 azure tts 的能力
[openai-tts](https://platform.openai.com/docs/guides/text-to-speech) 提供了类似 openai tts 的能力

#### Usage

你可以通过参数 `tts`, 来启用它

```yaml
tts: edge
```

For edge 查看更多语言支持, 从中选择一个

```shell
edge-tts --list-voices
```

#### 在容器中使用 edge-tts/azure-tts/openai-tts/volc/google/baidu

由于 Edge TTS 启动了一个本地的 HTTP 服务，所以需要将容器的端口映射到宿主机上，并且指定本地机器的 hostname:

```shell
docker run -v <your-config-dir>:/config -p 9527:9527 -e XIAOGPT_HOSTNAME=<your ip> yihong0618/xiaogpt --config=/config/config.yaml
```

注意端口必须映射为与容器内一致，XIAOGPT_HOSTNAME 需要设置为宿主机的 IP 地址，否则小爱无法正常播放语音。

## 推荐的类似项目

- [XiaoBot](https://github.com/longbai/xiaobot) -> Go语言版本的Fork, 带支持不同平台的UI
- [MiGPT](https://github.com/idootop/mi-gpt) -> Node.js 版，支持流式响应和长短期记忆

## 感谢

- [xiaomi](https://www.mi.com/)
- [PDM](https://pdm.fming.dev/latest/)
- [Tetos](https://github.com/frostming/tetos) TTS 云服务支持
- @[Yonsm](https://github.com/Yonsm) 的 [MiService](https://github.com/Yonsm/MiService)
- @[pjq](https://github.com/pjq) 给了这个项目非常多的帮助
- @[frostming](https://github.com/frostming) 重构了一些代码，支持了`持续会话功能`

## 赞赏

谢谢就够了
