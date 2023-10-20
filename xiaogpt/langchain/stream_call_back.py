import chardet
from queue import Queue
from typing import Any, Dict, List, Optional
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

DEFAULT_ANSWER_PREFIX_TOKENS = [""]
streaming_call_queue = Queue()


class StreamCallbackHandler(StreamingStdOutCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        token_copy = token
        code = chardet.detect(token_copy.encode())["encoding"]
        if code is not None:
            # Receive stream messages into the queue and dequeue when ask_stream
            streaming_call_queue.put(token)
