## ChatGPT-MiSpeaker
This python script is used to interact with OpenAI's ChatGPT model via the MiSpeaker. The script fetches questions from the MiSpeaker, passes the questions to the ChatGPT model, and returns the answers back to the MiSpeaker for TTS.

### Requirements
- python >= 3.6
- requests
- rich
- revChatGPT, https://github.com/acheong08/ChatGPT
- micli, MiService (https://github.com/Yonsm/MiService)

Please follow the revChatGPT/MiService to config your ChatGPT/MiService.
#### Update your ~/.bashrc or ~/.zshrc
```bash
export MI_USER="xxxxxxxxxx"
export MI_PASS="xxxxxxxx"
export MI_DID="114094xxx"
export MI_HARDWARE="S12A"
```

#### revChatGPT/config.json
```bash
cat ~/.config/revChatGPT/config.json
{
	"conversation_id": "c379851d-fbd4-479e-a716-xxxxxxxxxxxxx",
	"model": "text-davinci-002-render-sha",
	"paid":true,
	"verbose":true,
	"access_token":"xxxx"
}
```
- access_token: https://chat.openai.com/api/auth/session

### Usage
#### Clone the repository
```bash
git clone git@github.com:pjq/ChatGPT-MiSpeaker.git 
```
#### Install the requirements
```bash
pip3 install -r requirements.txt
```

#### Run the script
```bash
python3 ChatGPT-MiSpeaker.py --hardware "$MI_HARDWARE" --conversation_id="c379851d-fbd4-479e-a716-xxxxxxxxxxxx"
```
Replace HARDWARE with the identifier of your MiSpeaker, such as LX06, L05B, S12A, or LX01.

```bash
python3 ChatGPT-MiSpeaker.py --hardware "$MI_HARDWARE" --conversation_id="c379851d-fbd4-479e-a716-xxxxxxxxxxxx"
0
MiService: do_action 5-1: done, CompletedProcess(args=['micli', '5-1', '正在启动小爱同学和可爱无敌小朋友的语音助手的连接,请稍等哦'],
returncode=0)
ChatGPT:当然啦，皮皮虾！那让我们重新开始吧，从第一个单词开始！
0
MiService: do_action 5-1: done, CompletedProcess(args=['micli', '5-1', '当然啦，皮皮虾！那让我们重新开始吧，从第一个单词开始！'], returncode=0)
那开始吧
0
MiService: do_action 5-1: done, CompletedProcess(args=['micli', '5-1', '你的问题是那开始吧,请稍等哦，让我来想一想'], returncode=0)
Ask ChatGPT:那开始吧
ChatGPT:好啊，皮皮虾！让我们从头开始学习英文吧！首先，让我们来学一些常见的水果单词！，，Apple，-，苹果，Banana，-，香蕉，Grape，-，葡萄，
Peach，-，桃子，Strawberry，-，草莓，Watermelon，-，西瓜，，这些单词都很简单，你认识吗？我们可以一起读几遍，然后你试着说一说，如果有困难的地
方，我们再一起练习！
以下是小爱的回答:  开始干什么呢，小爱刚才没听清呢
0
MiService: do_action 5-1: done, CompletedProcess(args=['micli', '5-1',
'好啊，皮皮虾！让我们从头开始学习英文吧！首先，让我们来学一些常见的水果单词！，，Apple，-，苹果，Banana，-，香蕉，Grape，-，葡萄，Peach，-
，桃子，Strawberry，-，草莓，Watermelon，-，西瓜，，这些单词都很简单，你认识吗？我们可以一起读几遍，然后你试着说一说，如果有困难的地方，我们再
！'], returncode=0)
sleep: 33.6s
```

### Support
If you have any questions or issues, please open a new issue in the repository.