import uvicorn
from fastapi import FastAPI, Request
from Agent_Server_1.agent_server_1 import server_agent_1
from Agent_Server_2.agent_server_2 import server_agent_2
from config.settings import settings
from a2a.types import Message, TextPart, DataPart, Part
from uuid import uuid4
from contextlib import asynccontextmanager
from Agent_Client.client_a2a import create_client_for_agent, send_to_server_agent
import json
import zalo_bot
from until.webhook_zalo_bot import init_ngrok
from services.chat_service import ChatService
import asyncio
from until.enum import EventName


bot_zalo = zalo_bot.Bot(settings.BOOT_ZALO_TOKEN)

# bot_zalo.set_webhook(secret_token=settings.SECRET_TOKEN_WEBHOOK_ZALO, url= f"{ngrok_tunel_zalo_bot_webhook.public_url}/zalo/webhook")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent1_app = await server_agent_1.build()
    app.state.agent2_app = await server_agent_2.build()

    app.mount(settings.AGENT_1_PATH, app.state.agent1_app)
    app.mount(settings.AGENT_2_PATH, app.state.agent2_app)

    try:
        public_url = await init_ngrok(10000)
        await bot_zalo._set_webhook_async(
            url=f"{public_url}/zalo/webhook",
            secret_token=settings.SECRET_TOKEN_WEBHOOK_ZALO,
        )
        print("Webhook registered")

        yield

    finally:
        print("Shutdown...")


app = FastAPI(title="Currency Agent Platform", lifespan=lifespan)



# normal APIs
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/zalo/webhook")
async def zalo_webhook(req: Request):
    chat_service = ChatService()
    await chat_service.init()
    payload = await req.json()
    signature = req.headers.get("X-Zalo-Signature")

    print(f"signature {signature}")
    
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    

    chat_id = payload["message"]["chat"]["id"]

    message_id = payload["message"]["message_id"]

    event_name = payload.get("event_name")
    if event_name == EventName.Unsupported.value:
        await bot_zalo.send_message(chat_id=chat_id,text="Toi không hỗ trợ loại tin nhắn này",reply_to_message_id=message_id)
        return {"status": "ok"}
    elif event_name == EventName.Sticker.value:
        await bot_zalo.send_sticker(chat_id=chat_id,sticker="4591eff8d2bd3be362ac",reply_to_message_id=message_id)
        return {"status": "ok"}
    else:
        res = await chat_service.process_chat(user_id=chat_id, context_id="zalo_bot",
                                              user_input_text= payload["message"]["text"] if event_name==EventName.Text else None,
                                              user_input_photo = payload["message"]["photo_url"])

        print(message_id)

        print(f"Respose {res}")

        await bot_zalo.send_message(chat_id=chat_id,text= res[:1200],reply_to_message_id=message_id)


        return {"status": "ok"}


@app.get("/call_agents1")
async def call_agent_1():
    client, httpx_client = await create_client_for_agent(
        base_url= settings.BASE_URL + settings.AGENT_1_PATH,
        auth_token="my_secret_token" 
    )
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
    try:
        await send_to_server_agent(client, message)
    finally:
        await httpx_client.aclose()  

    return {"message": "This is a call to Agent 1"}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info", reload=True)
