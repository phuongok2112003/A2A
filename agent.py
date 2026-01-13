from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain import hub
def gen_agent_executor(llm,tools,context=None):
        llm_with_tools = llm.bind_tools(tools)

        # Chọn prompt dựa trên loại LLM
        # if isinstance(llm, ChatOpenAI):
        #     # Sử dụng prompt chuẩn cho OpenAI
        #     agent_prompt = hub.pull("hwchase17/openai-tools-agent")
        #     print(agent_prompt)
        # else:
            # Sử dụng prompt tùy chỉnh cho Gemini
        custom_system_message = f"""Bạn là một trợ lý hữu ích và thông minh.
    Bạn có khả năng trả lời các câu hỏi trực tiếp.
    Bạn cũng có thể sử dụng các công cụ sau đây để tìm kiếm thông tin hoặc thực hiện tác vụ:
    {context if context else ""}
"""
        print(f"\n\n\nprompt nao {custom_system_message}\n\n\n")

        agent_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", custom_system_message),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )

        # Tạo agent
        # Agent là "bộ não" quyết định khi nào và công cụ nào cần gọi.
        agent = create_tool_calling_agent(
            llm=llm_with_tools, # LLM đã được bind tools
            tools=tools,
            prompt=agent_prompt
        )


        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True, # Hiển thị các bước hoạt động của Agent
            handle_parsing_errors=True # Xử lý lỗi nếu LLM trả về định dạng không đúng
        )

class AgentCustom:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-pro", temperature=0.2
        )
    def invoke_agent(self):
        agent = gen_agent_executor(
            llm=self.llm,
            tools=[],
            context="Bạn có thể sử dụng các công cụ để hỗ trợ trả lời câu hỏi của người dùng."
        )
        return agent