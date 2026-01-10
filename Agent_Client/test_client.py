import asyncio
import httpx
from a2a.client import A2AClient
from a2a.types import SendMessageRequest, MessageSendParams
from uuid import uuid4

async def main():
    async with httpx.AsyncClient() as httpx_client:
        # 1. Kết nối tới Agent Server thông qua URL
        client = A2AClient(
            httpx_client, url='http://localhost:10000'
        )

        # 2. Chuẩn bị nội dung yêu cầu
        payload = {
            'message': {
                'role': 'user',
                'parts': [{'type': 'text', 'text': 'Chuyển đổi 100 USD sang VND'}],
                'messageId': uuid4().hex,
            }
        }

        # 3. Gửi tin nhắn và nhận phản hồi
        request = SendMessageRequest(  id=1,  
            jsonrpc="2.0",
               method="message/send",
            params=MessageSendParams(**payload))
        response = await client.send_message(request)
        print("Phản hồi từ Agent:", response)

if __name__ == "__main__":
    asyncio.run(main())
