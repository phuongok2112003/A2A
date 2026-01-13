from agent import AgentCustom
from config.settings import settings

agent = AgentCustom()

user_input = input("Bạn: ")

context_id = "test_context_123"  # Sử dụng một context_id cố định cho ví dụ này

response = agent.run(user_input = user_input, context_id=context_id)

print("Trợ lý:", response)

