# xiaogpt
Play ChatGPT with Xiaomi AI Speaker

![image](https://user-images.githubusercontent.com/15976103/220028375-c193a859-48a1-4270-95b6-ef540e54a621.png)


## 准备

1. ChatGPT id
2. 小爱音响
3. 能正常联网的环境或 proxy
4. python3.8+

## 使用

1. pip install -r requirements.txt
2. 参考 [MiService](https://github.com/Yonsm/MiService) 项目 README 并在本地 terminal 跑 `micli list` 拿到你音响的 DID 成功 **别忘了设置 export MI_DID=xxx** 这个 MI_DID 用 
3. 参考 [revChatGPT](https://github.com/acheong08/ChatGPT) 项目 README 配置 chatGPT 的 config
4. run `python xiaogpt.py --hardware ${your_hardware}` hardware 你看小爱屁股上有型号，输入进来
5. 跑起来之后就可以问小爱同学问题了，“帮我回答开头的问题” 会发送一份给 ChatGPT 然后小爱同学用 tts 回答
6. 如果你想用 conversation_id 来持续对话，可以加上 --conversation_id="xxxxxxxx"
7. 如果上面不可用，可以尝试用手机抓包，https://userprofile.mina.mi.com/device_profile/v2/conversation 找到 cookie 利用 --cookie '${cookie}' cookie 别忘了用单引号包裹
8. 默认用目前 ubus, 如果你的设备不支持 ubus 可以使用 --use_command 来使用 command 来 tts 

e.g.
```shell
python3 xiaogpt.py --hardware LX06;
# or
python3 xiaogpt.py --hardware LX06 --conversation_id="xxxxxxxx";
# or 
python3 xiaogpt.py --hardware LX06 --conversation_id="xxxxxxxx" --cookie ${cookie};
```

## QA

1. 用破解么？不用
2. 连不上 revChatGPT？国情，你得设置 proxy 并且该地区可用的 proxy
3. 你做这玩意也没用啊？确实。。。但是挺好玩的，有用对你来说没用，对我们来说不一定呀
4. 想把它变得更好？PR Issue always welcome.
5. 还有问题？提 Issuse 哈哈

## 赞赏

谢谢就够了
