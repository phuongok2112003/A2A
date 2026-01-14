import uvicorn
from fastapi import FastAPI
from Agent_Server_1.main import app as agent1_app
from Agent_Server_2.main import app as agent2_app
from config.settings import settings
from a2a.types import Message, TextPart, DataPart, Part
from uuid import uuid4
from Agent_Client.client_a2a import create_client_for_agent, send_to_server_agent
app = FastAPI(title="Currency Agent Platform")

# Mount A2A into FastAPI
app.mount(settings.AGENT_1_PATH, agent1_app)
app.mount(settings.AGENT_2_PATH, agent2_app)


# normal APIs
@app.get("/health")
def health():
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
