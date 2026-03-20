"""Mock heavy dependencies for testing."""

import sys
from unittest.mock import MagicMock

# langchain 1.x restructured submodules. Mock all submodules used by xiaogpt.
_mock_modules = [
    "langchain.memory",
    "langchain.agents",
    "langchain.tools",
    "langchain.callbacks",
    "langchain.callbacks.base",
    "langchain.chains",
    "langchain.schema",
    "langchain.schema.memory",
    "langchain.chat_models",
    "langchain.llms",
    "langchain.utilities",
    "langchain_community",
    "langchain_community.chat_models",
    "langchain_community.llms",
    "langchain_community.utilities",
    "miservice_fork",
    "zhipuai",
    "dashscope",
    "google.generativeai",
    "google.generativeai.types",
    "groq",
    "tetos",
    "tetos.base",
]

for mod_name in _mock_modules:
    sys.modules[mod_name] = MagicMock()
