import asyncio
import httpx
from uuid import uuid4
from a2a.client import A2AClient
from a2a.types import Message, TextPart, DataPart, SendStreamingMessageRequest


async def main():
    async with httpx.AsyncClient() as httpx_client:
        client = A2AClient(httpx_client, url="http://localhost:10000")

        # ✅ Tạo Message
        message = Message(
            messageId=uuid4().hex,
            role="user",
            parts=[
                TextPart(text="Convert currency"),
                DataPart(
                    data={
                        "amount": 100,
                        "from": "USD",
                        "to": "VND"
                    }
                )
            ]
        )

        # ✅ Tạo request
        request = SendStreamingMessageRequest(
            id=uuid4().hex,
            params={
                "skillId": "currency_conversion",
                "message": message
            }
        )

        print("📤 Sending currency conversion request...")

        try:
            async for response in client.send_message_streaming(request):
                result = response.root.result
                
                print("--------------------------------------------------")
                print(f"🔔 Received result: {result}")
                # Xử lý message từ agent
                if hasattr(result, 'message') and result.message:
                    for part in result.message.parts:
                        if hasattr(part, 'text'):
                            print(f"🤖 Agent: {part.text}")
                
                # Xử lý status update
                if hasattr(result, 'status'):
                    print(f"📊 Status: {result.status}")
                    if result.status == "completed":
                        print("✅ Task completed!")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
