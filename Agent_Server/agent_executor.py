from a2a.server.agent_execution import AgentExecutor

class CurrencyAgentExecutor(AgentExecutor):
    async def execute(self, context, event_queue):
        # Lấy tham số từ yêu cầu (ví dụ: amount, from_currency, to_currency)
        params = context.task.params
        amount = params.get("amount")
        
        # Gửi cập nhật trạng thái tạm thời cho bên yêu cầu
        await event_queue.send_message(f"Đang tính toán chuyển đổi cho {amount}...")
        
        # Giả lập logic chuyển đổi
        result = amount * 25000  # Ví dụ: USD sang VND
        
        # Trả về kết quả cuối cùng
        await event_queue.send_message(f"Kết quả: {result} VND")

    async def cancel(self, context, event_queue):
        print("Nhiệm vụ đã bị hủy.")
