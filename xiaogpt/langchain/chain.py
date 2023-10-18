from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.tools import BaseTool
from langchain.llms import OpenAI
from langchain import LLMMathChain, SerpAPIWrapper
from langchain.chat_models import ChatOpenAI
from langchain.memory import ChatMessageHistory
from xiaogpt.langchain.stream_call_back import StreamCallbackHandler
from langchain.agents.agent_toolkits import ZapierToolkit
from langchain.utilities.zapier import ZapierNLAWrapper
from xiaogpt.langchain.mail_box import Mailbox
from xiaogpt.langchain.mail_summary_tools import MailSummaryTool
from langchain.memory import ConversationBufferMemory

# from xiaogpt.config import Config


def agent_search(query):
    llm = ChatOpenAI(
        streaming=True,
        temperature=0,
        model="gpt-3.5-turbo-0613",
        callbacks=[StreamCallbackHandler()],
    )

    # Initialization: search chain, mathematical calculation chain, custom summary email chain
    search = SerpAPIWrapper()
    llm_math_chain = LLMMathChain(llm=llm, verbose=False)
    mail_summary = MailSummaryTool()

    # Tool list: search, mathematical calculations, custom summary emails
    tools = [
        Tool(name="Search", func=search.run, description="如果你不知道或不确定答案，可以使用这个搜索引擎检索答案"),
        Tool(name="Calculator", func=llm_math_chain.run, description="在需要回答数学问题时非常有用"),
        Tool(
            name="MailSummary",
            func=mail_summary.run,
            description="这是一个工具，订阅每天收到的邮件，总结并发送到我邮箱",
        ),
    ]

    agent = initialize_agent(
        tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=False
    )

    # query eg：'杭州亚运会中国队获得了多少枚金牌？' // '计算3的2次方' // '帮我总结今天收到的邮件'
    agent.run(query)
