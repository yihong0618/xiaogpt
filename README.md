# xiaogpt
play chatgpt with xiaomi ai speaker

## 准备

1. ChatGPT id
2. 小爱音响
3. 能正常联网的环境或 proxy
4. python3.8+
4. 抓包环境

## 使用

1. 在`小爱音响` APP 点对话记录并抓包找到 https://userprofile.mina.mi.com/device_profile/v2/conversation 这个 api 的 cookie
2. pip install -r requirements.txt
3. 参考 [MiService](https://github.com/Yonsm/MiService) 项目 README 并在本地 terminal 跑 `micli list` 拿到你音响的 DID 成功 **别忘了设置 export MI_DID=xxx** 这个 MI_DID 用 
4. 参考 [revChatGPT](https://github.com/acheong08/ChatGPT) 项目 README 配置 chatGPT 的 config
5. run `python xiaogpt.py ${cookie} --hardware ${your_hardware}` ${cookie} 为你抓包的 cookie hardware 你看小爱屁股上有型号，输入进来
6. 跑起来之后就可以问小爱同学问题了，“帮我回答开头的问题” 会发送一份给 ChatGPT 然后小爱同学用 tts 回答

## QA

1. 用破解么？不用
2. 为啥必须抓包？我之后再看看，争取不用抓包
3. 连不上 revChatGPT？国情，你得设置 proxy 并且该地区可用的 proxy
4. 你做这玩意也没用啊？确实。。。但是挺好玩的，有用对你来说没用，对我们来说不一定呀
5. 想把它变得更好？PR Issue always welcome.
6. 还有问题？提 Issuse 哈哈

## 赞赏

谢谢就够了
