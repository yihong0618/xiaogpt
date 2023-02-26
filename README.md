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
9. 使用 --mute_xiaoai 选项，可以让小爱不回答，但会频繁请求，玩一下可以使用，不建议一直用
10. 使用 --account ‘${account}’ --password ‘${password}’ 可以不进行步骤 2
11. 如果有能力可以自行替换唤醒词，也可以去掉唤醒词，源码 ` if query.find("帮我回答") != -1:`

e.g.
```shell
python3 xiaogpt.py --hardware LX06;
# or
python3 xiaogpt.py --hardware LX06 --conversation_id="xxxxxxxx";
# or 
python3 xiaogpt.py --hardware LX06 --conversation_id="xxxxxxxx" --cookie ${cookie};
# 如果你想直接输入账号密码
python3 xiaogpt.py --hardware LX06 --conversation_id="xxxxxxxx" --account ${your_xiaomi_account} --password ${your_password};
```

## 注意

1. 请开启小爱同学的蓝牙
2. 如果要更改提示词和 PROMPT 在代码最上面自行更改

## QA

1. 用破解么？不用
2. 连不上 revChatGPT？国情，你得设置 proxy 并且该地区可用的 proxy
3. 你做这玩意也没用啊？确实。。。但是挺好玩的，有用对你来说没用，对我们来说不一定呀
4. 想把它变得更好？PR Issue always welcome.
5. 还有问题？提 Issuse 哈哈

# 感谢

- [xiaomi](https://www.mi.com/)
- @[Yonsm](https://github.com/Yonsm) 的 [MiService](https://github.com/Yonsm/MiService) 

## 赞赏

谢谢就够了
