from __future__ import annotations

from langchain_classic.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.tools import Tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import LLMMathChain
from langchain_classic.base_memory import BaseMemory
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper


async def agent_search(
    query: str, memory: BaseMemory, callback: BaseCallbackHandler | None = None
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

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful AI assistant."),
            MessagesPlaceholder("history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = AgentExecutor(
        agent=create_openai_functions_agent(llm, tools, prompt),
        tools=tools,
        verbose=False,
        memory=memory,
    )
    callbacks = [callback] if callback else None
    # query eg：'杭州亚运会中国队获得了多少枚金牌？' // '计算 3 的 2 次方'
    result = await agent.ainvoke({"input": query}, config={"callbacks": callbacks})
    return result["output"]
