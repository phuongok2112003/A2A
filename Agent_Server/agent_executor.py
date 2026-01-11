from a2a.server.agent_execution import AgentExecutor
from a2a.types import Message, TextPart, Task, TaskStatus, TaskStatusUpdateEvent
from uuid import uuid4
import asyncio
class CurrencyAgentExecutor(AgentExecutor):

    async def execute(self, context, event_queue):
        try:
            print(f"[INFO] Starting execution")
            print(f"[INFO] Task ID: {context.task_id}")
            print(f"[INFO] Context ID: {context.context_id}")
            
            # ===== 1. Gửi Task object đầu tiên =====
            initial_task = Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state="working"),  # TaskStatus object
                message=context.message
            )
            print("[INFO] Sending initial task")
            await event_queue.enqueue_event(initial_task)
            
            # ===== 2. Lấy message từ context =====
            message = context.message
            print(f"[DEBUG] Message received with {len(message.parts)} parts")
            
            # ===== 3. Lấy data từ message parts =====
            data = None
            for part in message.parts:
                actual_part = part.root
                print(f"[DEBUG] Processing part kind: {actual_part.kind}")
                
                if actual_part.kind == "data":
                    data = actual_part.data
                    print(f"[DEBUG] Found data: {data}")

            if not data:
                print("[ERROR] No data part found")
                await event_queue.enqueue_event(
                    Message(
                        message_id=uuid4().hex,
                        role="agent",
                        parts=[TextPart(text="Missing currency data.")]
                    )
                )
                # Send completion status
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        id=uuid4().hex,
                        task_id=context.task_id,
                        context_id=context.context_id,
                        status=TaskStatus(state="completed"),
                        final=True
                    )
                )
                await event_queue.close()
                return

            # ===== 4. Extract values =====
            amount = float(data.get("amount", 0))
            from_ccy = data.get("from", "")
            to_ccy = data.get("to", "")

            print(f"[INFO] Converting: {amount} {from_ccy} -> {to_ccy}")

            # ===== 5. Send processing message =====
            await event_queue.enqueue_event(
                Message(
                    message_id=uuid4().hex,
                    role="agent",
                    parts=[TextPart(text=f"Converting {amount} {from_ccy} to {to_ccy}...")]
                )
            )


            await event_queue.enqueue_event(
                Message(
                    message_id=uuid4().hex,
                    role="agent",
                    parts=[TextPart(text=f"Converting {amount} {from_ccy} to {to_ccy} hihihihihihihdfd===")]
                )
            )
            # ===== 6. Business logic =====
            if from_ccy == "USD" and to_ccy == "VND":
                rate = 25400
            elif from_ccy == "VND" and to_ccy == "USD":
                rate = 1 / 25400
            else:
                rate = 1

            result = amount * rate
            print(f"[INFO] Conversion result: {result}")

            # ===== 7. Send result =====
            await event_queue.enqueue_event(
                Message(
                    message_id=uuid4().hex,
                    role="agent",
                    parts=[TextPart(text=f"Result: {amount} {from_ccy} = {result:,.0f} {to_ccy}")]
                )
            )

            # ===== 8. Send completion status =====
            print("[INFO] Sending completion status")
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    id=uuid4().hex,
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(state="completed"),
                    final=True
                )
            )

            # ===== 9. Close queue =====
            print("[INFO] Closing event queue")
            print("[INFO] Waiting for events to flush...")
            await asyncio.sleep(5)  # Đợi 0.5 giây để dữ liệu kịp đẩy xuống Client
            await event_queue.close()
            print("[INFO] Task completed successfully")

        except Exception as e:
            print(f"[ERROR] Executor failed: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                await event_queue.enqueue_event(
                    Message(
                        messageId=uuid4().hex,
                        role="agent",
                        parts=[TextPart(text=f"Agent error: {str(e)}")]
                    )
                )
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        id=uuid4().hex,
                        taskId=context.task_id,
                        contextId=context.context_id,
                        status=TaskStatus(state="failed"),
                        final=True
                    )
                )
                await event_queue.close()
            except Exception as e2:
                print(f"[ERROR] Failed to send error message: {e2}")
                try:
                    await event_queue.close(immediate=True)
                except:
                    pass

    async def cancel(self, context, event_queue):
        print("[INFO] Task cancelled")
        try:
            await event_queue.enqueue_event(
                Message(
                    messageId=uuid4().hex,
                    role="agent",
                    parts=[TextPart(text="Task was cancelled")]
                )
            )
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    id=uuid4().hex,
                    taskId=context.task_id,
                    contextId=context.context_id,
                    status=TaskStatus(state="cancelled"),
                    final=True
                )
            )
            await event_queue.close()
        except Exception as e:
            print(f"[ERROR] Cancel failed: {e}")