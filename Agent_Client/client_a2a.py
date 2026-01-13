import asyncio
import httpx
from uuid import uuid4
from pprint import pprint

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig, Client
from a2a.types import Message, TextPart, DataPart, AgentCard, Part
from config.settings import settings


async def create_client_for_agent(base_url: str, auth_token: str | None = None) -> Client:
    
    httpx_client = httpx.AsyncClient(timeout=30.0)

    resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)

    
    public_card: AgentCard = await resolver.get_agent_card()
    print(f"✅ Fetched Public Agent Card from {base_url}: {public_card.name}")

    private_card = public_card  

    
    if public_card.supports_authenticated_extended_card and auth_token:
        try:
            private_card = await resolver.get_agent_card(
                relative_card_path='/agent/authenticatedExtendedCard',
                http_kwargs={"headers": {"Authorization": f"Bearer {auth_token}"}}
            )
            print(f"✅ Fetched Private Extended Card: {private_card.name}")
        except Exception as e:
            print(f"⚠️ Failed to fetch private card: {e}. Using public card.")

    # Tạo client từ factory
    config = ClientConfig(httpx_client=httpx_client)
    factory = ClientFactory(config)
    client = factory.create(private_card)

    return client, httpx_client


async def send_to_server_agent(client : Client, message : Message):
    print("Sending request...")
    try:
        async for task, update in client.send_message(request=message):
                print(f"Task: {task}")
                print(f"Update: {update}")
                if task:
                    # snapshot của task
                    if task.status and task.status.message:
                        for p in task.status.message.parts:
                            print("Task:", p.root.text)

                if update:
                    if update.kind == "status-update":
                        if update.status and update.status.message:
                            for p in update.status.message.parts:
                                print("Status:", p.root.text)

                    elif update.kind == "artifact-update":
                        if update.artifact:
                            for p in update.artifact.parts:
                                print("Artifact:", p.root.text)

                    elif update.kind == "message":
                        for p in update.parts:
                            print("Message:", p.root.text)

                    if getattr(update, "final", False):
                        print("Stream completed")
                        break

    except Exception as e:
        print(f"❌ Currency Error: {e}")
        import traceback
        traceback.print_exc()


# async def main():

#     client_agent_1 = await create_client_for_agent(
#         base_url= settings.BASE_URL + settings.AGENT_1_PATH,
#         auth_token="my_secret_token" 
#     )


#     client_agent_2 = await create_client_for_agent(
#         base_url= settings.BASE_URL + settings.AGENT_2_PATH,
#         auth_token="my_secret_token" 
#     )


