import asyncio
import httpx
from uuid import uuid4
from a2a.client import A2AClient
from a2a.types import Message, TextPart, DataPart


async def main():
    async with httpx.AsyncClient() as httpx_client:
        client = A2AClient(httpx_client, url="http://localhost:10000")


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

        stream = await client.send_message_streaming(
            agent_name="CurrencyExpert",
            skill_id="currency_conversion",
            message=message
        )

        async for event in stream:
            if event.type == "message":
                print("Agent:", event.message.parts[0].text)
            elif event.type == "task_complete":
                print("Task finished")


if __name__ == "__main__":
    asyncio.run(main())
