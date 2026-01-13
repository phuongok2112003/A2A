import asyncio
import httpx
from uuid import uuid4
from a2a.client import A2AClient, A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, TextPart, DataPart, SendStreamingMessageRequest, AgentCard
import pprint

async def main():
    async with httpx.AsyncClient() as httpx_client:
        PUBLIC_AGENT_CARD_PATH = '/.well-known/agent-card.json'
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
            context_id="1db07da4-02e7-4156-a0f9-4d4f14783758",
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
                print(f"Task: {task}")
                print(f"Update: {update}")
                if task:
                    # snapshot của task
                    if task.status and task.status.message:
                        for p in task.status.message.parts:
                            print("📦 Task:", p.root.text)

                if update:
                    if update.kind == "status-update":
                        if update.status and update.status.message:
                            for p in update.status.message.parts:
                                print("📊 Status:", p.root.text)

                    elif update.kind == "artifact-update":
                        if update.artifact:
                            for p in update.artifact.parts:
                                print("📦 Artifact:", p.root.text)

                    elif update.kind == "message":
                        for p in update.parts:
                            print("🤖 Message:", p.root.text)

                    if getattr(update, "final", False):
                        print("✅ Stream completed")
                        break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
