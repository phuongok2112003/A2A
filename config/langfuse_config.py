from langfuse.langchain import CallbackHandler
from langfuse import Langfuse, propagate_attributes
from config.settings import settings
from functools import wraps
from schemas.base import ConfigConversation
# Start Langfuse 
langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    base_url=settings.LANGFUSE_BASE_URL
)

langfuse_handler = CallbackHandler()


def handler_session_langfuse(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with langfuse.start_as_current_observation(as_type="span", name="langchain-call"):
            # Propagate session_id to all observations
            configConverstation : ConfigConversation = kwargs.get("config_conversation")
            with propagate_attributes(session_id= configConverstation.context_id, user_id=configConverstation.user_id):
                async for item in func(*args, **kwargs):
                    yield item

    return wrapper