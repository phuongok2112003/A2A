import asyncio
import httpx
from uuid import uuid4
from a2a.client import A2AClient, A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, TextPart, DataPart, SendStreamingMessageRequest, AgentCard
import pprint

async def main():
    async with httpx.AsyncClient() as httpx_client:
        PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'
        PRIVATE_AGENT_CARD_PATH = '/agent/authenticatedExtendedCard'
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url="http://localhost:10000",
            agent_card_path=PUBLIC_AGENT_CARD_PATH
        )
        agent_card: AgentCard = await resolver.get_agent_card()
        pprint.pp(f"✅ Fetched Agent Card: {agent_card}")

        if agent_card.supports_authenticated_extended_card:
            private_card = await resolver.get_agent_card(
                relative_card_path=PRIVATE_AGENT_CARD_PATH,
                http_kwargs={ "headers": { "Authorization": "Bearer my_secret_token" } }
            )
            pprint.pp(f"✅ Fetched Private Agent Card: {private_card}")

      
        config = ClientConfig(httpx_client=httpx_client)
        factory = ClientFactory(config)

        client = factory.create(private_card)

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
                "message": message
            }
        )

        print("📤 Sending currency conversion request...")

        try:
            async for task, update in client.send_message(request=message):
                print(f"Task {task}")
                print(f"Update {update}")
                if update:  # Ưu tiên event update nếu có
                    text = update.status.message.parts if update.status.message else ""
                    print("🤖 Agent update:", text)
                elif task and task.status.message:
                    text = task.status.message.parts
                    print("🤖 Task status:", text)
                
                if update and update.final:
                    print("✅ Stream completed!")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
