from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.tools import BaseTool
from langchain.llms import OpenAI
from langchain.chains import LLMMathChain
from langchain.utilities import SerpAPIWrapper
from langchain.chat_models import ChatOpenAI
from langchain.memory import ChatMessageHistory
from xiaogpt.langchain.stream_call_back import StreamCallbackHandler
from langchain.agents.agent_toolkits import ZapierToolkit
from langchain.utilities.zapier import ZapierNLAWrapper
from langchain.memory import ConversationBufferMemory


def agent_search(query):
    llm = ChatOpenAI(
        streaming=True,
        temperature=0,
        model="gpt-3.5-turbo-0613",
        callbacks=[StreamCallbackHandler()],
    )

    # Initialization: search chain, mathematical calculation chain
    search = SerpAPIWrapper()
    llm_math_chain = LLMMathChain.from_llm(llm=llm, verbose=False)

    # Tool list: search, mathematical calculations
    tools = [
        Tool(name="Search", func=search.run, description="如果你不知道或不确定答案，可以使用这个搜索引擎检索答案"),
        Tool(name="Calculator", func=llm_math_chain.run, description="在需要回答数学问题时非常有用"),
    ]

    agent = initialize_agent(
        tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=False
    )

    # query eg：'杭州亚运会中国队获得了多少枚金牌？' // '计算3的2次方'
    agent.run(query)
