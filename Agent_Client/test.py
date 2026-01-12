import asyncio
import httpx
from uuid import uuid4
from pprint import pprint

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig, Client
from a2a.types import Message, TextPart, DataPart, AgentCard


async def create_client_for_agent(base_url: str, auth_token: str | None = None) -> tuple[AgentCard, Client]:
    """Tạo client cho một agent cụ thể (public + private nếu có)"""
    async with httpx.AsyncClient(timeout=30.0) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)

        # Fetch public card
        public_card: AgentCard = await resolver.get_agent_card()
        print(f"✅ Fetched Public Agent Card from {base_url}: {public_card.name}")

        private_card = public_card  # Default fallback

        # Nếu agent hỗ trợ extended card và có token
        if public_card.supports_authenticated_extended_card and auth_token:
            try:
                private_card = await resolver.get_agent_card(
                    relative_card_path="/agent/authenticatedExtendedCard",
                    http_kwargs={"headers": {"Authorization": f"Bearer {auth_token}"}}
                )
                print(f"✅ Fetched Private Extended Card: {private_card.name}")
            except Exception as e:
                print(f"⚠️ Failed to fetch private card: {e}. Using public card.")

        # Tạo client từ factory
        config = ClientConfig(httpx_client=httpx_client)
        factory = ClientFactory(config)
        client = factory.create(private_card)

        return private_card, client


async def test_currency_agent(client : Client, message_text: str = "Convert 100 USD to VND"):
    """Test CurrencyExpert agent"""
    print("\n" + "="*50)
    print("📤 Testing CurrencyExpert (currency conversion)")
    print("="*50)

    # Tạo message với data part
    message = Message(
        message_id=uuid4().hex,
        role="user",
        parts=[
            TextPart(text=message_text),
            DataPart(
                data={
                    "amount": 100,
                    "from": "USD",
                    "to": "VND"
                }
            )
        ]
    )

    print("Sending request...")
    try:
        async for task, update in client.send_message(request=message):
            if update and update.status and update.status.message:
                text = update.status.message.parts[0].root.text
                print(f"🤖 Agent: {text}")

            if update and update.final:
                print("✅ Currency task completed!")
                break

    except Exception as e:
        print(f"❌ Currency Error: {e}")
        import traceback
        traceback.print_exc()


async def test_travel_agent(client : Client, message_text: str = "Recommend places to visit in Vietnam for 5 days with $500 budget"):
    """Test TravelBuddy agent"""
    print("\n" + "="*50)
    print("📤 Testing TravelBuddy (travel recommendation)")
    print("="*50)

    message = Message(
        message_id=uuid4().hex,
        role="user",
        parts=[TextPart(text=message_text)]
    )

    print("Sending request...")
    try:
        async for task, update in client.send_message(request=message):
            if update and update.status and update.status.message:
                text = update.status.message.parts[0].root.text
                print(f"🤖 TravelBuddy: {text}")

            if update and update.final:
                print("✅ Travel task completed!")
                break

    except Exception as e:
        print(f"❌ Travel Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    # Agent 1: CurrencyExpert - port 10000
    currency_card, currency_client = await create_client_for_agent(
        base_url="http://localhost:10000",
        auth_token="my_secret_token"  # Thay bằng token thật nếu cần
    )

    # Agent 2: TravelBuddy - port 10001
    travel_card, travel_client = await create_client_for_agent(
        base_url="http://localhost:10001",
        auth_token="my_secret_token"  # Nếu TravelBuddy cần auth
    )

    # Test cả hai agent
    await test_currency_agent(currency_client)
    await test_travel_agent(travel_client)

    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())