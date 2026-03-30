# from agent import AgentCustom
# from config.settings import settings
# from common.tool_common import tools, interrupt_on_tool

# access_agent_urls = [
#     settings.BASE_URL + settings.AGENT_1_PATH, settings.BASE_URL + settings.AGENT_2_PATH,
# ]
# async def main():

    # context_id = "fresh_conversation_008"  # Sử dụng một context_id cố định cho ví dụ này
    # user_id = "user_124"
    # agent = await AgentCustom.create(
    #         access_agent_urls=access_agent_urls,
    #         tools=tools,
    #         interrupt_on_tool=interrupt_on_tool
    #     )
    
    # agent.get_info_tool()
    
    # # user_input = input("Bạn: ")
    # user_input = "Bạn hãy clone project https://github.com/phuongok2112003/shop-online.git cho tôi"
    # # response = await agent.run(user_input = user_input, context_id=context_id)
    # # print("Trợ lý:", response)

    # # async for res in agent.run_astream(user_input=user_input, context_id=context_id):
    # #    print(res)

    # async for res in agent.run_astream(
    #     user_input_text=user_input,
    #     context_id=context_id,
    #     user_id=user_id
    # ):
    #     print("Trợ lý:",res)

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"
model_id = "microsoft/bitnet-b1.58-2B-4T"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16
)

# Apply the chat template
messages = [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user", "content": "Tôi muốn biết tổng thống hiện tại của Mỹ là ai?"},
]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
chat_input = tokenizer(prompt, return_tensors="pt").to(model.device)


# Generate response
chat_outputs = model.generate(**chat_input, max_new_tokens=50)
response = tokenizer.decode(chat_outputs[0][chat_input['input_ids'].shape[-1]:], skip_special_tokens=True) # Decode only the response part
print("\nAssistant Response:", response)
