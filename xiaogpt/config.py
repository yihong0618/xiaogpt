LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"

HARDWARE_COMMAND_DICT = {
    "LX06": "5-1",
    "L05B": "5-3",
    "S12A": "5-1",
    "LX01": "5-1",
    "L06A": "5-1",
    "LX04": "5-1",
    "L05C": "5-3",
    "L17A": "7-3",
    "X08E": "7-3",
    "LX05A": "5-1",  # 小爱红外版
    "LX5A": "5-1",  # 小爱红外版
    # add more here
}
MI_USER = ""
MI_PASS = ""
OPENAI_API_KEY = ""
KEY_WORD = ["帮我", "请回答"]
PROMPT = "请用100字以内回答"
# simulate_xiaoai_question
MI_ASK_SIMULATE_DATA = {
    "code": 0,
    "message": "Success",
    "data": '{"bitSet":[0,1,1],"records":[{"bitSet":[0,1,1,1,1],"answers":[{"bitSet":[0,1,1,1],"type":"TTS","tts":{"bitSet":[0,1],"text":"Fake Answer"}}],"time":1677851434593,"query":"Fake Question","requestId":"fada34f8fa0c3f408ee6761ec7391d85"}],"nextEndTime":1677849207387}',
}
