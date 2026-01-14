from collections import ChainMap

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
