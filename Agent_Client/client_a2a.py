import asyncio
import httpx
from uuid import uuid4
from pprint import pprint

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig, Client
from a2a.types import Message, TextPart, DataPart, AgentCard, Part
from config.settings import settings
from typing import Tuple, Optional
from a2a.client.middleware import ClientCallContext, ClientCallInterceptor
from typing import Any
class BearerAuthInterceptor(ClientCallInterceptor):
    def __init__(self, auth_token: str):
        self.auth_token = auth_token

    async def intercept(
        self,
        method_name: str,
        request_payload: dict[str, Any],
        http_kwargs: dict[str, Any],
        agent_card,
        context: ClientCallContext | None,
    ):
        headers = http_kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.auth_token}"
        http_kwargs["headers"] = headers
        return request_payload, http_kwargs

async def create_client_for_agent(base_url: str, auth_token: str | None = None) ->Tuple[Client, httpx.AsyncClient, AgentCard, AgentCard]:
    PUBLIC_AGENT_CARD_PATH = '/.well-known/agent-card.json'
    PRIVATE_AGENT_CARD_PATH = '/agent/authenticatedExtendedCard'
    httpx_client = httpx.AsyncClient(timeout=30.0)

    resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url, agent_card_path=PUBLIC_AGENT_CARD_PATH)

    public_card: AgentCard = await resolver.get_agent_card()


    private_card = public_card  

    
    if public_card.supports_authenticated_extended_card and auth_token:
        try:
            print("Fetching private agent card with authentication...")
            private_card = await resolver.get_agent_card(
                relative_card_path=PRIVATE_AGENT_CARD_PATH,
                http_kwargs={"headers": {"Authorization": f"Bearer {auth_token}"}}
            )
          
        except Exception as e:
            print(f"⚠️ Failed to fetch private card: {e}. Using public card.")

    # Tạo client từ factory
    config = ClientConfig(httpx_client=httpx_client)
    factory = ClientFactory(config)
    interceptors = []
    if auth_token:
        interceptors.append(BearerAuthInterceptor(auth_token))
    client = factory.create(private_card, interceptors=interceptors)

    return client, httpx_client, public_card, private_card


async def send_to_server_agent(client : Client, message : Message,  auth_token: str | None = None,):
    print("Sending request...")
    context = None
    if auth_token:
        context = ClientCallContext(
            state={
                "http_kwargs": {
                    "headers": {
                        "Authorization": f"Bearer {auth_token}"
                    }
                }
            }
        )
    try:
        async for task, update in client.send_message(request=message, context=context):
                if task:
                    # snapshot của task
                    if task.status and task.status.message:
                        for p in task.status.message.parts:
                            print("Task:", p.root.text)
                            yield {
                                "task": task,
                                "update": None,
                                "final": False,
                                "text": p.root.text
                            }

                if update:
                    if update.kind == "status-update":
                        if update.status and update.status.message:
                            for p in update.status.message.parts:
                                print("Status:", p.root.text)
                                yield {
                                    "task": task,
                                    "update": update,
                                    "final": False,
                                    "text": p.root.text
                                }

                    elif update.kind == "artifact-update":
                        if update.artifact:
                            for p in update.artifact.parts:
                                print("Artifact:", p.root.text)
                                yield {
                                    "task": task,
                                    "update": update,
                                    "final": False,
                                    "text": p.root.text
                                }

                    elif update.kind == "message":
                        for p in update.parts:
                            print("Message:", p.root.text)
                            yield {
                                "task": task,
                                "update": update,
                                "final": False,
                                "text": p.root.text
                            }

                    if getattr(update, "final", False):
                        print("Stream completed")
                        if update.kind == "status-update":
                            if update.status and update.status.message:
                                for p in update.status.message.parts:
                                    yield {
                                        "task": task,
                                        "update": update,
                                        "final": True,
                                        "text": p.root.text
                                    }
                        break

    except Exception as e:
        print(f"❌ Currency Error: {e}")
        import traceback
        traceback.print_exc()