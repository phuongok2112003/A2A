from typing import Callable
from a2a.server.agent_execution import AgentExecutor
from agent import AgentCustom
from typing import List, Optional
from abc import ABC, abstractmethod
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, DataPart
from a2a.utils import new_agent_text_message, new_task
from schemas.base import ServerAgentRequest
from until.convert import dict_to_string
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue

class BaseAgentExecutor(AgentExecutor, ABC):
    def __init__(
        self,
        access_agent_urls: List[str] = [],
        tools: List = [Callable],
        interrupt_on_tool: List = [Callable],
    ):
        super().__init__()
        self.agent: Optional[AgentCustom] = None
        self.access_agent_urls = access_agent_urls
        self.tools = tools
        self.interrupt_on_tool = interrupt_on_tool

    async def create_agent(self):
        if self.agent is None:
            self.agent = await AgentCustom.create(
                access_agent_urls=self.access_agent_urls,
                tools=self.tools,
                interrupt_on_tool=self.interrupt_on_tool,
            )

    @abstractmethod
    async def execute(self,  context: RequestContext, event_queue: EventQueue):
        pass

    @abstractmethod
    async def cancel(self,  context: RequestContext, event_queue: EventQueue):
        pass

    async def run_astream_in_agent_server(
        self,
        server_agent: ServerAgentRequest,
        client: TaskUpdater | None = None,
    ):
        config = {
            "configurable": {"thread_id": server_agent.context_id},
            "recursion_limit": self.agent.recursion_limit,
        }
        input_user:str = None
        user_id:str
        data_command: dict = None
        task_finished = False
        final_state = None
        for part in server_agent.input_payload.parts:
            if isinstance(part.root, DataPart):
                data = part.root.data
                if data["type"] == "input_user":
                    input_user = data["data"]
                elif data["type"] == "user_id":
                    user_id = data["data"]
                elif data["type"] == "command":
                    data_command = data["data"]
                else:
                    raise ValueError("Invalid input payload")

        # # ===== INPUT =====
        # part = server_agent.input_payload.parts[0]
        # if isinstance(part.root, DataPart):
        #     data = part.root.data
        # else:
        #     raise ValueError("Invalid input payload")
        if input_user:
            print(f"User inpuit ở A2A {input_user}")
            graph_input = {"messages": [HumanMessage(content=input_user)]}

        elif data_command:
            print(f"User inpuidata_command  ở A2A {data_command}")
            graph_input = Command(resume=data_command)

        async for mode, payload in self.agent.agent.astream(
            graph_input,
            context={"user_id": user_id} if user_id else "guest",
            config=config,
            stream_mode=["values", "updates", "messages"],
        ):
            # ===== INTERRUPT =====
            if "__interrupt__" in payload and not task_finished:
                interrupt_event = payload["__interrupt__"][0]
                hitl_request = interrupt_event.value

                task_finished = True
                await client.update_status(
                    state=TaskState.input_required,
                    message=new_agent_text_message(
                        dict_to_string(hitl_request),
                        server_agent.context_id,
                        server_agent.task_id,
                    ),
                )
                return

            # ===== FINAL STATE =====
            if mode == "values" and not task_finished:
                final_state = payload

        # ===== COMPLETED =====
        if final_state and not task_finished:
            for msg in reversed(final_state.get("messages", [])):
                if isinstance(msg, AIMessage):
                    task_finished = True
                    await client.update_status(
                        state=TaskState.completed,
                        message=new_agent_text_message(
                            msg.content,
                            server_agent.context_id,
                            server_agent.task_id,
                        ),
                    )
                    print("[INFO] Task completed successfully")
                    return
