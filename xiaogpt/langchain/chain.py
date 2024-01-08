from __future__ import annotations

from langchain.agents import AgentType, Tool, initialize_agent
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import LLMMathChain
from langchain.schema.memory import BaseMemory
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper


async def agent_search(
    query: str, memeory: BaseMemory, callback: BaseCallbackHandler | None = None
) -> str:
    llm = ChatOpenAI(
        streaming=True,
        temperature=0,
        model="gpt-3.5-turbo-0613",
    )

    # Initialization: search chain, mathematical calculation chain
    search = SerpAPIWrapper()
    llm_math_chain = LLMMathChain.from_llm(llm=llm, verbose=False)

    # Tool list: search, mathematical calculations
    tools = [
        Tool(
            name="Search",
            func=search.run,
            description="如果你不知道或不确定答案，可以使用这个搜索引擎检索答案",
        ),
        Tool(
            name="Calculator",
            func=llm_math_chain.run,
            description="在需要回答数学问题时非常有用",
        ),
    ]

    agent = initialize_agent(
        tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=False, memory=memeory
    )
    callbacks = [callback] if callback else None
    # query eg：'杭州亚运会中国队获得了多少枚金牌？' // '计算3的2次方'
    return await agent.arun(query, callbacks=callbacks)
