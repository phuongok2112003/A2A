from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.base import get_checkpoint_id
from elasticsearch import Elasticsearch
from typing import Any, Optional, List, Dict, Tuple
from datetime import datetime
from until.convert import normalize as convert_normalize, extract_persistable_config

class ElasticsearchCheckpointSaver(BaseCheckpointSaver[int]):
    def __init__(self, es: Elasticsearch, index: str = "langgraph_checkpoints"):
        super().__init__()
        self.es = es
        self.index = index

    # -------------------------------
    # Get latest checkpoint
    # -------------------------------
    async def aget_tuple(self, config):
        thread_id = config["configurable"]["thread_id"]

        res = self.es.search(
            index=self.index,
            size=1,
            sort=[{"ts": {"order": "desc"}}],
            query={"term": {"thread_id": thread_id}},
        )

        if not res["hits"]["hits"]:
            return None

        doc = res["hits"]["hits"][0]["_source"]
        return self._doc_to_tuple(doc)

    # -------------------------------
    # List checkpoints
    # -------------------------------
    async def alist(self, config, *, filter=None, before=None, limit=None):
        thread_id = config["configurable"]["thread_id"] if config else None

        query = {"match_all": {}}
        if thread_id:
            query = {"term": {"thread_id": thread_id}}

        res = self.es.search(
            index=self.index,
            size=limit or 100,
            sort=[{"ts": {"order": "asc"}}],
            query=query,
        )

        for hit in res["hits"]["hits"]:
            yield self._doc_to_tuple(hit["_source"])

    # -------------------------------
    # Put checkpoint
    # -------------------------------
    async def aput(self, config, checkpoint, metadata, new_versions):
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]
        
        safe_config = extract_persistable_config(config)
        safe_checkpoint = convert_normalize(checkpoint)
        safe_metadata = convert_normalize(metadata) if metadata else None



        doc = {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "ts": checkpoint["ts"],
            "config": self.serde.dumps(safe_config).decode("utf-8"),
            "checkpoint": self.serde.dumps(safe_checkpoint).decode("utf-8"),
            "metadata": self.serde.dumps(safe_metadata).decode("utf-8") if safe_metadata else None,
            "channel_versions": self.serde.dumps(new_versions).decode("utf-8"),
            "channel_versions": self.serde.dumps(new_versions).decode("utf-8"),
        }

        self.es.index(index=self.index, id=f"{thread_id}:{checkpoint_id}", document=doc)

        # update config with checkpoint_id
        config = dict(config)
        config["configurable"] = dict(config.get("configurable", {}))
        config["configurable"]["checkpoint_id"] = checkpoint_id
        return config

    # -------------------------------
    # Put intermediate writes
    # -------------------------------
    def put_writes(self, config: Dict[str, Any], writes: List[Tuple[str, Any]], task_id: str):
        """
        Lưu các kết quả trung gian (VD: kết quả từ Tool gọi về).
        Nếu thiếu hàm này, ainvoke sẽ lỗi NotImplementedError.
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"]["checkpoint_id"]

        # Serialize danh sách writes
        safe_writes = [(channel, convert_normalize(value)) for channel, value in writes]
        serialized_writes = self.serde.dumps(safe_writes).decode("utf-8")

        doc = {
            "type": "writes", # Đánh dấu đây là dữ liệu writes
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "task_id": task_id,
            "writes": serialized_writes,
            "ts": datetime.now().isoformat()
        }

        # Lưu vào ES với ID riêng biệt
        self.es.index(index=self.index, id=f"{thread_id}:{checkpoint_id}:{task_id}", document=doc)

    def aput_writes(self, config, writes, task_id, task_path=""):
        return self.put_writes(config, writes, task_id)
    # -------------------------------
    # Delete thread
    # -------------------------------
    async def adelete_thread(self, thread_id):
        self.es.delete_by_query(
            index=self.index,
            query={"term": {"thread_id": thread_id}},
        )

    # -------------------------------
    # Helpers
    # -------------------------------
    def _doc_to_tuple(self, doc):
        from langgraph.checkpoint.base import CheckpointTuple

        return CheckpointTuple(
            config=self.serde.loads(doc["config"]),
            checkpoint=self.serde.loads(doc["checkpoint"]),
            metadata=self.serde.loads(doc["metadata"]),
            parent_config=None,
            pending_writes=None,
        )
