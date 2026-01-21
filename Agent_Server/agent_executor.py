from typing import Callable
from a2a.server.agent_execution import AgentExecutor
from agent import AgentCustom
from typing import List, Optional
from abc import ABC, abstractmethod
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command  
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message, new_task
from schemas.base import ServerAgentRequest
from until.convert import dict_to_string
class BaseAgentExecutor(AgentExecutor, ABC):
    def __init__(self,access_agent_urls: List[str] = [], tools: List = [Callable], interrupt_on_tool: List = [Callable]):
        super().__init__()
        self.agent : Optional[AgentCustom] = None
        self.access_agent_urls = access_agent_urls
        self.tools = tools
        self.interrupt_on_tool = interrupt_on_tool
 
    async def create_agent(self):
        if self.agent is None:
            self.agent = await AgentCustom.create(
                access_agent_urls=self.access_agent_urls, tools=self.tools,interrupt_on_tool=self.interrupt_on_tool
            )

    @abstractmethod
    async def execute(self, context, event_queue):
        pass
    @abstractmethod
    async def cancel(self, context, event_queue):
        pass
    
    async def run_astream_in_agent_server(self, server_agent:ServerAgentRequest,  client : TaskUpdater | None = None):
       
        config = {
            "configurable": {"thread_id": server_agent.context_id},
            "recursion_limit": self.agent.recursion_limit,
        }
        print(f"==========================Type in stram{server_agent.input_payload.type}========================")

        async for mode, payload in self.agent.agent.astream(
            server_agent.input_payload.data if  server_agent.input_payload.type =="text" else Command(resume=server_agent.input_payload.data),
            config=config,
            stream_mode=["values", "updates", "messages"],
        ):
            # giữ state cuối
            if mode == "values":
                final_state = payload

            # ===== INTERRUPT =====
            if "__interrupt__" in payload:
                interrupt_event = payload["__interrupt__"][0]
                hitl_request = interrupt_event.value
                print(f"=======================payload:{dict_to_string(hitl_request)}========================")
                await client.update_status(
                        state=TaskState.input_required,
                        message=new_agent_text_message(dict_to_string(hitl_request),server_agent.context_id, server_agent.task_id)
                    )
                   
        # ===== FINAL ANSWER =====
        # if final_state:
        #     for msg in reversed(final_state["messages"]):
        #         if isinstance(msg, AIMessage):
        #             await client.update_status(
        #                     state=TaskState.completed,
        #                     message=new_agent_text_message(msg.content,server_agent.context_id, server_agent.task_id)
        #                 )
        #             # return msg.content
                    
