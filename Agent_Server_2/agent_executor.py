from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import uuid4
from typing import List
from a2a.server.agent_execution import AgentExecutor
from .tools import tools
from a2a.types import (
    Task,
    TaskStatus,
    TaskStatusUpdateEvent,
    Message,
    TextPart,
)
from agent import AgentCustom

class CurrencyAgentExecutor(AgentExecutor):
    """
    Currency conversion agent using A2A task-based streaming.
    - Sends initial Task → multiple TaskStatusUpdateEvent → final status with final=True.
    - All messages wrapped in TaskStatus.message (Message object).
    - Fixed: Added required 'final' field to TaskStatusUpdateEvent.
    """

    def __init__(self):
        super().__init__()
        self.agent = None  # No internal agent needed for this executor
    
    @classmethod
    async def create(cls, access_agent_urls: List[str] = [], **kwargs) -> CurrencyAgentExecutor:
        self = cls(**kwargs)
        self.agent = await AgentCustom.create(
            access_agent_urls=access_agent_urls,
        )
        return self

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
            print("[INFO] Starting currency conversion task")
            print(f"[INFO] Task ID: {context.task_id}")
            print(f"[INFO] Context ID: {context.context_id}")

            # 1. Send initial Task (required)
            initial_task = Task(
                id=context.task_id,
                context_id=context.context_id,
                status=self._create_status(
                    "working",
                    "Received conversion request. Processing..."
                ),
                message=context.message,  # Keep original user message
            )
            print("[INFO] Enqueuing initial Task")
            await event_queue.enqueue_event(initial_task)

            # 2. Extract data from message parts
            data = None
            for part in context.message.parts:
                actual_part = part.root
                if actual_part.kind == "data":
                    data = actual_part.data
                    print(f"[DEBUG] Found data: {data}")
                    break

            if not data:
                print("[ERROR] No data part found")
                await self._send_error_and_complete(
                    event_queue, context, "Missing or invalid currency data.", final=True
                )
                return

            # 3. Parse amount and currencies
            try:
                amount = float(data.get("amount", 0))
                from_ccy = data.get("from", "").upper()
                to_ccy = data.get("to", "").upper()
            except (ValueError, TypeError):
                await self._send_error_and_complete(
                    event_queue, context, "Invalid amount or currency code.", final=True
                )
                return

            if amount <= 0 or not from_ccy or not to_ccy:
                await self._send_error_and_complete(
                    event_queue, context, "Amount must be positive and currencies required.", final=True
                )
                return

            print(f"[INFO] Converting: {amount} {from_ccy} → {to_ccy}")

            # 4. Send processing update (final=False vì chưa xong)
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=self._create_status(
                        "working",
                        f"Converting {amount} {from_ccy} to {to_ccy}..."
                    ),
                    final=False,  # Explicitly set (though default may be False)
                )
            )

            # 5. Business logic
            if from_ccy == "USD" and to_ccy == "VND":
                rate = 25400.0
            elif from_ccy == "VND" and to_ccy == "USD":
                rate = 1 / 25400.0
            else:
                rate = 1.0  # Fallback

            result = amount * rate
            await asyncio.sleep(0.4)  # Simulate delay

            # 6. Send final result (final=True)
            result_text = (
                f"Conversion completed!\n"
                f"{amount:,.2f} {from_ccy} = {result:,.0f} {to_ccy}\n"
                f"Exchange rate: {rate:,.4f}"
            )
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=self._create_status("completed", result_text),
                    final=True,  # Required for final event
                )
            )

            # 7. Flush and close
            print("[INFO] Flushing events...")
            await asyncio.sleep(0.6)
            print("[INFO] Closing event queue")
            await event_queue.close()

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