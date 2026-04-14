import json
from langchain.agents.middleware.shell_tool import _SessionResources
from collections import ChainMap, deque
from typing import Any
import time, httpx, asyncio
def normalize(obj):
    if isinstance(obj, ChainMap):
        # Merge all layers into one dict
        merged = {}
        for m in reversed(obj.maps):
            merged.update(m)
        return normalize(merged)

    elif isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items()}

    elif isinstance(obj, (list, tuple)):
        return [normalize(v) for v in obj]

    else:
        return obj
def extract_persistable_config(config):
    cfg = {}

    configurable = config.get("configurable", {})
    if isinstance(configurable, ChainMap):
        configurable = dict(configurable)

    cfg["configurable"] = {
        k: v for k, v in configurable.items()
        if k in ("thread_id", "checkpoint_id")
    }

    return cfg



def convert_deque(obj: Any) -> Any:
    """
    Recursively convert deque to list and handle other non-serializable types
    """
    if isinstance(obj, deque):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: convert_deque(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_deque(item) for item in obj]
    elif isinstance(obj, set):
        return list(obj)
    else:
        return obj


def is_safe_to_serialize(obj: Any) -> bool:
    """
    Check if object is safe to serialize
    """
    unsafe_types = (
        'httpx',
        'Session',
        '_SessionResources',
        'Connection',
        'Socket',
        'Lock',
        'Thread',
        'Database',
        'Engine',
    )
    
    obj_type = type(obj).__name__
    obj_module = type(obj).__module__
    
    return not any(
        unsafe in obj_type or unsafe in obj_module
        for unsafe in unsafe_types
    )


def dict_to_string(data: dict) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,   # giữ tiếng Việt
        separators=(",", ":") # gọn, ổn định
    )

def string_to_dict(text: str) -> dict:
    return json.loads(text)
