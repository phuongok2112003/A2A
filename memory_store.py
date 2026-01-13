from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
class MemoryStore:
    def __init__(self):
        self.memories = {}

    def get_memory(self, context_id: str) -> BaseChatMessageHistory:
        if context_id not in self.memories:
            self.memories[context_id] = InMemoryChatMessageHistory()
        return self.memories[context_id]