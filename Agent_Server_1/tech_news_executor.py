from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import uuid4
from typing import List

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
from Agent_Server.agent_executor import BaseAgentExecutor


class TechNewsExecutor(BaseAgentExecutor):
    """
    Agent executor chuyên biệt cho việc tìm kiếm và tổng hợp tin tức công nghệ.

    Tính năng:
    - Tự động tìm kiếm tin tức công nghệ trong ngày
    - Tổng hợp và trình bày kết quả một cách chuyên nghiệp
    - Hỗ trợ tìm kiếm theo chủ đề (AI, lập trình, phần mềm, phần cứng, v.v.)
    """

    def __init__(self, access_agent_urls: List[str] = [], tools: List = []):
        super().__init__(access_agent_urls=access_agent_urls, tools=tools)

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
        """
        Thực thi task tìm kiếm tin tức công nghệ.

        Flow:
        1. Parse user input để xác định chủ đề và số ngày
        2. Gọi các tools phù hợp để tìm kiếm tin tức
        3. Tổng hợp kết quả và trả về dưới dạng markdown
        """
        try:
            await self.create_agent()
            print("[INFO] Starting technology news search task")
            print(f"[INFO] Task ID: {context.task_id}")
            print(f"[INFO] Context ID: {context.context_id}")

            task = context.current_task
            if not task:
                print("[INFO] Creating initial task from message")
                task = new_task(context.message)

            print("[INFO] Enqueuing initial Task")
            await event_queue.enqueue_event(task)
            updater = TaskUpdater(
                event_queue=event_queue,
                task_id=task.id,
                context_id=task.context_id
            )

            await updater.update_status(
                state="working",
                message=new_agent_text_message(
                    "Đang tìm kiếm tin tức công nghệ mới nhất...",
                    task.context_id,
                    task.id
                )
            )

            # Parse user input
            user_input = context.get_user_input()
            topic = "technology"  # Mặc định
            days = 1  # Mặc định hôm nay

            # Try to extract topic from user input
            if isinstance(user_input, str):
                user_input_lower = user_input.lower()
                topics_map = {
                    "ai": "ai",
                    "lập trình": "programming",
                    "code": "programming",
                    "phần mềm": "software",
                    "phần cứng": "hardware",
                    "công nghệ": "technology",
                    "machine learning": "ai",
                }
                for keyword, topic_name in topics_map.items():
                    if keyword in user_input_lower:
                        topic = topic_name
                        break

            # Try to extract number of days
            import re
            days_match = re.search(r"(\d+)\s*(ngày|day)", user_input_lower)
            if days_match:
                days = int(days_match.group(1))

            print(f"[DEBUG] Topic: {topic}, Days: {days}")

            # Gọi agent với tools tìm kiếm công nghệ
            prompt = f"""
Hãy tìm kiếm và tổng hợp tin tức công nghệ mới nhất về chủ đề "{topic}" trong {days} ngày gần đây.

Sử dụng các tool sau để tìm kiếm:
1. get_today_tech_news("{topic}", {days}) - untuk tin tức chuyên biệt
2. search_internet("{topic} công nghệ mới nhất hôm nay", "advanced") - để tìm thông tin chi tiết

Yêu cầu:
- Trả về danh sách tin tức với tiêu đề, URL và tóm tắt
- Nếu tìm được nhiều tin, chỉ chọn 5-10 tin nổi bật nhất
- Trình bày dưới dạng markdown dễ đọc
- Nếu không tìm được tin nào, nói rõ và gợi ý một chủ đề khác

Ngày hiện tại: {datetime.now().strftime('%Y-%m-%d')}
"""

            result_text = await self.agent.run(user_input=prompt, context_id=context.context_id)

            print(f"[INFO] Technology news search result: {result_text[:200]}...")
            await updater.update_status(
                state="completed",
                message=new_agent_text_message(result_text, task.context_id, task.id)
            )

            await event_queue.close()
            print("[INFO] Technology news task completed successfully")

        except Exception as e:
            print(f"[ERROR] TechNewsExecutor failed: {e}")
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
                final=final,
            )
        )
        await asyncio.sleep(0.4)
        await event_queue.close()
        print("[INFO] Error sent and task completed with failure")

    async def cancel(self, context, event_queue):
        print("[INFO] Technology news task cancelled by client")
        try:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=self._create_status(
                        "canceled",
                        "Technology news task was cancelled by user."
                    ),
                    final=True,
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
