# xiaogpt

[![PyPI](https://img.shields.io/pypi/v/xiaogpt?style=flat-square)](https://pypi.org/project/xiaogpt)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/yihong0618/xiaogpt?color=%23086DCD&label=docker%20image)](https://hub.docker.com/r/yihong0618/xiaogpt)

<https://user-images.githubusercontent.com/15976103/226803357-72f87a41-a15b-409e-94f5-e2d262eecd53.mp4>

Play ChatGPT and other LLM with Xiaomi AI Speaker

![image](https://user-images.githubusercontent.com/15976103/220028375-c193a859-48a1-4270-95b6-ef540e54a621.png)
![image](https://user-images.githubusercontent.com/15976103/226802344-9c71f543-b73c-4a47-8703-4c200c434dec.png)

## 支持的 AI 类型

LLM 调用统一由 [Republic](https://getrepublic.org) 完成，支持 [Republic 的所有 provider](https://getrepublic.org/providers/)，包括：

- 内置 provider：OpenAI、Anthropic、Google Gemini、DeepSeek、Moonshot（Kimi）、智谱 GLM（`zai`）、OpenRouter、Ollama 等
- OpenAI 兼容服务：通义千问、豆包、Groq、PPIO 派欧云、接口AI 等

## 获取小米音响 DID

| 系统和 Shell   | Linux *sh                                      | Windows CMD 用户                        | Windows PowerShell 用户                         |
| ------------- | ---------------------------------------------- | -------------------------------------- | ---------------------------------------------- |
| 1、安装包     | `pip install miservice==3.0.1`                   | `pip install miservice==3.0.1`           | `pip install miservice==3.0.1`                   |
| 2、设置变量   | `export MI_USER=xxx` <br> `export MI_PASS=xxx` | `set MI_USER=xxx`<br>`set MI_PASS=xxx` | `$env:MI_USER="xxx"` <br> `$env:MI_PASS="xxx"` |
| 3、取得 MI_DID | `miservice list`                                   | `miservice list`                           | `miservice list`                                   |
| 4、设置 MI_DID | `export MI_DID=xxx`                            | `set MI_DID=xxx`                       | `$env:MI_DID="xxx"`                            |

- 注意不同 shell 对环境变量的处理是不同的，尤其是 powershell 赋值时，可能需要双引号来包括值。
- 如果获取 did 报错时，请更换一下无线网络，有很大概率解决问题。

## 一点原理

[不用 root 使用小爱同学和 ChatGPT 交互折腾记](https://github.com/yihong0618/gitblog/issues/258)

## 准备

1. LLM 服务的 API key
2. 小爱音响
3. 能正常联网的环境或 proxy
4. Python 3.12–3.14

## 使用

- `pip install -U --force-reinstall xiaogpt[locked]`
- 参考官方 [MiService](https://github.com/Yonsm/MiService) 项目 README 并在本地 terminal 跑 `miservice list` 拿到你音响的 DID 成功 **别忘了设置 export MI_DID=xxx** 这个 MI_DID 用
- 官方 MiService 会优先读取当前用户的 `~/.mi.token`，仅在 token 缺失或认证被拒绝时登录，重新认证会先用保存的 passToken 续期。首次登录或 passToken 也失效时可能需要在交互终端输入短信/邮件验证码；可先运行 `miservice mina` 完成登录。可通过环境变量 `XIAOGPT_MI_TOKEN_PATH` 修改 xiaogpt 使用的 token 路径，Docker 部署见下方说明；有效 token 下重启无需重新输入验证码。升级已有环境时先卸载 `miservice-fork`，避免两个发行包共用 `miservice` 模块造成冲突，再安装项目依赖。
- run `xiaogpt --hardware ${your_hardware}` hardware 你看小爱屁股上有型号，输入进来，如果在屁股上找不到或者型号不对，可以用 `miservice mina` 找到型号
- 跑起来之后就可以问小爱同学问题了，“帮我”或“请”开头的问题，会发送一份给 LLM 然后小爱同学用 tts 回答
- 如果上面不可用，可以尝试用手机抓包，<https://userprofile.mina.mi.com/device_profile/v2/conversation> 找到 cookie 利用 `--cookie '${cookie}'` cookie 别忘了用单引号包裹
- 默认用目前 ubus, 如果你的设备不支持 ubus 可以使用 `--use_command` 来使用 command 来 tts
- 使用 `--mute_xiaoai` 选项，可以快速停掉小爱的回答
- 使用 `--account ${account} --password ${password}`
- 如果有能力可以自行替换唤醒词，也可以去掉唤醒词
- LLM 调用统一使用 [Republic](https://getrepublic.org)，用 `--model provider:model` 指定模型，默认 `openai:gpt-4o-mini`。支持的 provider 见 [Republic provider 列表](https://getrepublic.org/providers/)，如 `openai`、`anthropic`、`google`、`deepseek`、`moonshot`、`zai`、`openrouter`、`ollama` 等
- 用 `--api_key` 指定 API key，不指定时读取环境变量 `REPUBLIC_<PROVIDER>_API_KEY`（如 `REPUBLIC_DEEPSEEK_API_KEY`）；`openai` 还兼容旧的 `OPENAI_API_KEY`
- 如果你遇到了墙需要用 Cloudflare Workers 替换 api_base 请使用 `--api_base ${url}` 来替换。 **请注意，此处你输入的 api 应该是'`https://xxxx/v1`'的字样，域名需要用引号包裹**
- 其他 OpenAI 兼容的服务（通义千问、豆包、Groq、PPIO、接口AI 等）用 `openai:<模型名> --api_base <服务地址> --api_format chat` 接入
- 可以跟小爱说 `开始持续对话` 自动进入持续对话状态，`结束持续对话` 结束持续对话状态。
- 可以使用 `--tts edge` 来获取更好的 tts 能力
- 可以使用 `--tts fish --fish_api_key <your-fish-key> --fish_voice_key <fish-voice>` 来获取 [fish-audio](https://fish.audio/) 能力 (如何获取 fish voice 见下)
- 可以使用 `--tts openai`、`--tts azure` 等第三方 TTS，所需的 key 等参数通过配置文件中的 `tts_options` 传入，见下方 [第三方 TTS](#第三方-tts)

e.g.

```shell
export OPENAI_API_KEY=${your_api_key}
xiaogpt --hardware LX06
# or
xiaogpt --hardware LX06 --cookie ${cookie}
# 如果你想直接输入账号密码
xiaogpt --hardware LX06 --account ${your_xiaomi_account} --password ${your_password}
# 如果你想 mute 小米的回答
xiaogpt --hardware LX06  --mute_xiaoai
# 使用流式响应，获得更快的响应
xiaogpt --hardware LX06  --mute_xiaoai --stream
# 如果你想使用 google 的 gemini
xiaogpt --hardware LX06  --mute_xiaoai --model google:gemini-2.0-flash --api_key ${gemini_key}
# 如果你想使用 DeepSeek
xiaogpt --hardware LX06  --mute_xiaoai --model deepseek:deepseek-chat --api_key ${deepseek_key}
# 如果你想使用 kimi
xiaogpt --hardware LX06  --mute_xiaoai --model moonshot:kimi-latest --api_key ${moonshot_api_key}
# 如果你想使用智谱 GLM（国内平台需指定 api_base）
xiaogpt --hardware LX06  --mute_xiaoai --model zai:glm-4-flash --api_base https://open.bigmodel.cn/api/paas/v4 --api_key ${glm_key}
# 如果你想使用阿里的通义千问（OpenAI 兼容接口）
xiaogpt --hardware LX06  --mute_xiaoai --model openai:qwen-plus --api_format chat --api_base https://dashscope.aliyuncs.com/compatible-mode/v1 --api_key ${qwen_key}
# 如果你想使用豆包（OpenAI 兼容接口，模型名填推理接入点 ID）
xiaogpt --hardware LX06  --mute_xiaoai --model openai:${endpoint_id} --api_format chat --api_base https://ark.cn-beijing.volces.com/api/v3 --api_key ${ark_api_key}
# 如果你想使用 Groq 的 llama
xiaogpt --hardware LX06  --mute_xiaoai --model openai:llama-3.3-70b-versatile --api_format chat --api_base https://api.groq.com/openai/v1 --api_key ${groq_key}
# 如果你想使用 PPIO 派欧云（接口AI 把 api_base 换成 https://api.jiekou.ai/openai）
xiaogpt --hardware LX06  --mute_xiaoai --model openai:deepseek/deepseek-v3.2 --api_format chat --api_base https://api.ppinfra.com/openai --api_key ${ppio_api_key}
```

使用 git clone 运行，先用 [PDM](https://pdm-project.org/) 安装依赖，再把上面的 `xiaogpt` 换成 `pdm run xiaogpt` 即可：

```shell
pdm install
export OPENAI_API_KEY=${your_api_key}
pdm run xiaogpt --hardware LX06
```

## config.yaml

如果想通过单一配置文件启动也是可以的，可以通过 `--config` 参数指定配置文件，config 文件必须是合法的 YAML 或 JSON 格式。

参数优先级：命令行参数 > 配置文件 > 默认值

```shell
cp xiao_config.yaml.example xiao_config.yaml
# 编辑 xiao_config.yaml 后
xiaogpt --config xiao_config.yaml
```

若要指定模型参数，如 temperature, top_p, max_tokens, 请在 config.yaml 中指定：

```yaml
gpt_options:
  temperature: 0.9
  top_p: 0.9
```

可用参数见 [Republic ChatOptions](https://getrepublic.org/reference/provider-api/)，服务特有的参数可以放到 `extra_body` 中。

## 配置项说明

| 参数                  | 说明                                                                    | 默认值                                           |
| --------------------- | ----------------------------------------------------------------------- | ------------------------------------------------ |
| hardware              | 设备型号                                                                | `LX06`                                           |
| account               | 小米账户，也可用环境变量 `MI_USER`                                      |                                                  |
| password              | 小米账户密码，也可用环境变量 `MI_PASS`                                  |                                                  |
| cookie                | 小米账户 cookie（如果用上面密码登录可以不填）                           |                                                  |
| mi_did                | 设备 did，也可用环境变量 `MI_DID`                                       |                                                  |
| model                 | 模型，格式为 `provider:model`，参考 [Republic providers](https://getrepublic.org/providers/) | `openai:gpt-4o-mini`         |
| api_key               | 模型服务的 API key，不填则读取 `REPUBLIC_<PROVIDER>_API_KEY`            |                                                  |
| api_base              | 替换默认的 API 地址，例如 `https://xxxx/v1`                             |                                                  |
| api_format            | 对话接口格式：`chat`、`responses`、`messages`，OpenAI 兼容服务用 `chat` | provider 默认格式                                |
| gpt_options           | 模型调用参数字典，如 `temperature`、`top_p`、`max_tokens`               | `{}`                                             |
| prompt                | 自定义 prompt，作为 system 消息发送                                     | `以下请用 300 字以内回答，请只回答文字不要带链接` |
| keyword               | 自定义请求词列表                                                        | `["帮我", "请"]`                                 |
| change_prompt_keyword | 更改提示词触发列表                                                      | `["更改提示词"]`                                 |
| start_conversation    | 开始持续对话关键词                                                      | `开始持续对话`                                   |
| end_conversation      | 结束持续对话关键词                                                      | `结束持续对话`                                   |
| stream                | 使用流式响应，获得更快的响应                                            | `false`                                          |
| mute_xiaoai           | 快速停掉小爱自己的回答                                                  | `false`                                          |
| use_command           | 使用 MI command 与小爱交互                                              | `false`                                          |
| verbose               | 打印详细日志                                                            | `0`                                              |
| proxy                 | HTTP 代理地址，如 `http://localhost:8080`                               |                                                  |
| tts                   | TTS 类型：`mi`、`edge`、`openai`、`azure`、`volc`、`baidu`、`google`、`minimax`、`fish` | `mi`                             |
| tts_options           | TTS 参数字典，参考 [tetos](https://github.com/frostming/tetos) 获取可用参数 | `{}`                                         |
| volc_access_key       | 火山引擎 TTS 的 access key，请在[这里](https://console.volcengine.com/iam/keymanage/)获取 |                                |
| volc_secret_key       | 火山引擎 TTS 的 secret key                                              |                                                  |

## 注意

1. 请开启小爱同学的蓝牙
2. 提示词可以用 `prompt` 配置项修改，也可以对小爱说「更改提示词」+ 新的提示词临时修改
3. 目前已知 LX04、X10A 和 L05B L05C 可能需要使用 `--use_command`，否则可能会出现终端能输出 GPT 的回复但小爱同学不回答 GPT 的情况。这几个型号也只支持小爱原本的 tts.
4. 在 wsl 使用时，需要设置代理为 <http://wsl 的 ip:port(vpn 的代理端口)>, 否则会出现连接超时的情况，详情 [报错：Error communicating with OpenAI](https://github.com/yihong0618/xiaogpt/issues/235)

## QA

1. 用破解么？不用
2. 你做这玩意也没用啊？确实。。。但是挺好玩的，有用对你来说没用，对我们来说不一定呀
3. 想把它变得更好？PR Issue always welcome.
4. 还有问题？提 Issue 哈哈
5. Exception: Error <https://api2.mina.mi.com/admin/v2/device_list?master=0&requestId=app_ios_xxx>: Login failed [@KJZH001](https://github.com/KJZH001)<br>
   这是由于小米风控导致，海外地区无法登录大陆的账户，请尝试 cookie 登录
   无法抓包的可以在本地部署完毕项目后再用户文件夹`C:\Users\用户名`下面找到.mi.token，然后扔到你无法登录的服务器去<br>
   若是 linux 则请放到当前用户的 home 文件夹，此时你可以重新执行先前的命令，不出意外即可正常登录（但 cookie 可能会过一段时间失效，需要重新获取）<br>
   详情请见 [https://github.com/yihong0618/xiaogpt/issues/332](https://github.com/yihong0618/xiaogpt/issues/332)

## 视频教程

<https://www.youtube.com/watch?v=K4YA8YwzOOA>

## Docker

### 常规用法

X86/ARM Docker Image: `yihong0618/xiaogpt`

容器设置了 `XIAOGPT_MI_TOKEN_PATH=/config/.mi.token`，登录 token 会保存到 `/config/.mi.token`。请把宿主机上可写的目录挂载到 `/config`，并保持下面示例中的 `-v <your-config-dir>:/config`；已有 token 请先复制到 `<your-config-dir>/.mi.token`。首次登录或 passToken 失效后可能需要验证码，可先用 `-it` 在前台运行一次，按提示输入验证码，token 保存后再正常运行：

```shell
docker run -it --rm -v <your-config-dir>:/config -e OPENAI_API_KEY=<your-openapi-key> yihong0618/xiaogpt <命令行参数>
```

```shell
docker run -v <your-config-dir>:/config -e OPENAI_API_KEY=<your-openapi-key> yihong0618/xiaogpt <命令行参数>
```

如

```shell
docker run -v <your-config-dir>:/config -e OPENAI_API_KEY=<your-openapi-key> yihong0618/xiaogpt --account=<your-xiaomi-account> --password=<your-xiaomi-password> --hardware=<your-xiaomi-hardware>
```

### 使用配置文件

xiaogpt 的配置文件可通过指定 volume /config，以及指定参数--config 来处理，如

```shell
docker run -v <your-config-dir>:/config yihong0618/xiaogpt --config=/config/config.yaml
```

### 网络使用 host 模型

```shell
docker run -v <your-config-dir>:/config --network=host yihong0618/xiaogpt --config=/config/config.yaml
```

### 本地编译 Docker Image

```shell
 docker build -t xiaogpt .
```

如果需要在 Apple Silicon 上编译 x86 镜像

```shell
 docker buildx build --platform=linux/amd64 -t xiaogpt-x86 .
```

### 第三方 TTS

除了小爱自带的 TTS，还可以通过 [tetos](https://github.com/frostming/tetos) 使用以下第三方 TTS：

- [edge-tts](https://github.com/rany2/edge-tts)：免费，无需 key
- [openai-tts](https://platform.openai.com/docs/guides/text-to-speech)
- [azure-tts](https://learn.microsoft.com/azure/ai-services/speech-service/text-to-speech)
- [fish-tts](https://fish.audio/)
- 火山引擎（volc）、百度（baidu）、Google（google）、MiniMax（minimax）

#### Usage

你可以通过参数 `tts` 来启用它，需要 key 的 TTS 通过 `tts_options` 传参，可用参数见 [tetos](https://github.com/frostming/tetos)：

```yaml
tts: edge
# 或者
tts: openai
tts_options:
  api_key: sk-xxxx
  api_base: https://api.openai.com/v1
```

For edge 查看更多语言支持，从中选择一个

```shell
edge-tts --list-voices
```

#### 如果你想使用 [fish-tts](https://fish.audio/)

1. 注册 https://fish.audio/zh-CN/go-api/ 拿到 api key
2. 选择你想要的声音自建声音或者使用热门声音  https://fish.audio/zh-CN/text-to-speech/?modelId=e80ea225770f42f79d50aa98be3cedfc 其中 `e80ea225770f42f79d50aa98be3cedfc` 就声音的 key id
3. `xiaogpt --hardware LX06 --account xxxx --password xxxxx --mute_xiaoai --stream --tts fish --fish_api_key xxxxx --fish_voice_key xxxxx`
4. 或者在 xiao_config.yaml 中配置

```yaml
tts: fish
# TTS 参数字典，参考 https://github.com/frostming/tetos 获取可用参数
tts_options:
  api_key: xxxxx
  voice: xxxxx
```

#### 在容器中使用 edge-tts/azure-tts/openai-tts/volc/google/baidu/fish

由于第三方 TTS 会启动一个本地的 HTTP 服务供小爱拉取音频，所以需要将容器的端口映射到宿主机上，并且指定本地机器的 hostname:

```shell
docker run -v <your-config-dir>:/config -p 9527:9527 -e XIAOGPT_HOSTNAME=<your ip> yihong0618/xiaogpt --config=/config/config.yaml
```

注意端口必须映射为与容器内一致，XIAOGPT_HOSTNAME 需要设置为宿主机的 IP 地址，否则小爱无法正常播放语音。

## 推荐的类似项目

- [XiaoBot](https://github.com/longbai/xiaobot) -> Go 语言版本的 Fork, 带支持不同平台的 UI
- [MiGPT](https://github.com/idootop/mi-gpt) -> Node.js 版，支持流式响应和长短期记忆

## 感谢

- [xiaomi](https://www.mi.com/)
- [PDM](https://pdm-project.org/)
- [Republic](https://getrepublic.org) LLM 调用
- [Tetos](https://github.com/frostming/tetos) TTS 云服务支持
- @[Yonsm](https://github.com/Yonsm) 的 [MiService](https://github.com/Yonsm/MiService)
- @[pjq](https://github.com/pjq) 给了这个项目非常多的帮助
- @[frostming](https://github.com/frostming) 重构了一些代码，支持了`持续会话功能`

## 赞赏

谢谢就够了
