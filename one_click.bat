@echo off
cd C:\xxx\xiaogpt-main
set MI_USER=1234556
set MI_PASS=1234556
set MI_DID=1234556
set OPENAI_API_KEY=1234556

call activate torchenv
python xiaogpt.py --hardware LX06  --mute_xiaoai --use_gpt3

cmd /k
