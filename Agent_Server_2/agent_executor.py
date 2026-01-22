from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor
from a2a.types import (
    Task,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    Message,
    TextPart,
    Artifact
)
from a2a.utils import new_agent_text_message, new_task
from a2a.server.tasks import TaskUpdater
from agent import AgentCustom
from .tools import tools
from typing import List
from Agent_Server.agent_executor import BaseAgentExecutor
from typing import Callable
from schemas.base import ServerAgentRequest
from until.convert import string_to_dict
class CurrencyAgentExecutor(BaseAgentExecutor):
    """
    Currency conversion agent using A2A task-based streaming.
    - Sends initial Task → multiple TaskStatusUpdateEvent → final status with final=True.
    - All messages wrapped in TaskStatus.message (Message object).
    - Fixed: Added required 'final' field to TaskStatusUpdateEvent.
    """
    def __init__(self,access_agent_urls: List[str] = [], tools: List = [Callable], interrupt_on_tool: List = [Callable]):
        super().__init__(access_agent_urls=access_agent_urls, tools=tools, interrupt_on_tool=interrupt_on_tool)
       
    def _create_status(self, state: str, text: str) -> TaskStatus:
        """Helper to create TaskStatus with correct Message object."""
        return TaskStatus(
            state=state,
            message=Message(
                message_id=uuid4().hex,
                role="agent",
                parts=[TextPart(text=text)],
            ),
            timestamp=datetime.utcnow().isoformat() + "Z",  # ISO 8601 UTC
        )

    async def execute(self, context, event_queue):
        try:
            await self.create_agent()
            print("[INFO] Starting currency conversion task")
            print(f"[INFO] Task ID: {context.task_id}")
            print(f"[INFO] Context ID: {context.context_id}")
            print(f"[DEBUG] Message parts: {context.get_user_input()}")
            

            task = context.current_task
            if not task:
                print("[INFO] Creating initial task from message")
                task = new_task(context.message)

            print(f"[INFO] Enqueuing initial Task {context.message}")
            await event_queue.enqueue_event(task)
            updater = TaskUpdater(event_queue = event_queue,task_id = task.id,context_id = task.context_id)


            await updater.update_status(
                state="working",
                message=new_agent_text_message("Processing currency conversion...",task.context_id, task.id)
            )
            
            request_agent = ServerAgentRequest(context_id=task.context_id, task_id= task.id,
                                               input_payload=context.message)

            await self.run_astream_in_agent_server(client=updater,server_agent=request_agent)
       
            # await updater.update_status(
            #     state="completed",
            #     message=new_agent_text_message(result_text,task.context_id, task.id)
            # )


            # # await updater.complete()
            # await event_queue.close()

            print("[INFO] Task completed successfully")

        except Exception as e:
            print(f"[ERROR] Executor failed: {e}")
            import traceback
            traceback.print_exc()
            await self._send_error_and_complete(
                event_queue, context, f"Internal error: {str(e)}", final=True
            )

    async def _send_error_and_complete(self, event_queue, context, error_text: str, final: bool = True):
        """Send error status and complete task cleanly."""
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=self._create_status("failed", error_text),
                final=final,  # Always True for error/completion
            )
        )
        await asyncio.sleep(0.4)
        await event_queue.close()
        print("[INFO] Error sent and task completed with failure")

    async def cancel(self, context, event_queue):
        print("[INFO] Task cancelled by client")
        try:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=self._create_status(
                        "canceled",
                        "Task was cancelled by user."
                    ),
                    final=True,  # Required for cancel
                )
            )
            await asyncio.sleep(0.4)
            await event_queue.close()
            print("[INFO] Cancel completed")
        except Exception as e:
            print(f"[ERROR] Cancel failed: {e}")
            try:
                await event_queue.close(immediate=True)
            except:
                pass