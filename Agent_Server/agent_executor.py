from a2a.server.agent_execution import AgentExecutor

class CurrencyAgentExecutor(AgentExecutor):

    async def execute(self, context, event_queue):
        try:
            # ===== 1. Lấy structured data từ message.parts =====
            data = None
            for part in context.task.message.parts:
                if part.type == "data":
                    data = part.data

            if not data:
                await event_queue.send_message("Missing currency data.")
                await event_queue.complete()
                return

            amount = float(data["amount"])
            from_ccy = data["from"]
            to_ccy = data["to"]

            await event_queue.send_message(
                f"Converting {amount} {from_ccy} to {to_ccy}..."
            )

            # ===== 2. Business logic (mock FX rate) =====
            if from_ccy == "USD" and to_ccy == "VND":
                rate = 25400
            else:
                rate = 1

            result = amount * rate

            # ===== 3. Gửi kết quả =====
            await event_queue.send_message(
                f"Result: {amount} {from_ccy} = {result:,.0f} {to_ccy}"
            )

            # ===== 4. Kết thúc task =====
            await event_queue.complete()

        except Exception as e:
            await event_queue.send_message(f"Agent error: {e}")
            await event_queue.complete()

    async def cancel(self, context, event_queue):
        print("Task cancelled")
