"""
Elasticsearch Checkpoint Saver for LangGraph
Lưu trữ checkpoint của LangGraph agent vào Elasticsearch
"""

from typing import Any, AsyncIterator, Iterator, Optional, Sequence
from elasticsearch import Elasticsearch
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)
from langchain_core.runnables import RunnableConfig
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
import base64


class ElasticsearchCheckpointSaver(BaseCheckpointSaver[str]):
    """
    Checkpoint Saver sử dụng Elasticsearch làm backend storage.
    
    Args:
        es: Elasticsearch client instance
        index: Tên index trong Elasticsearch (mặc định: "langgraph_checkpoints")
    
    Example:
        ```python
        from elasticsearch import Elasticsearch
        from memory.elasticsearch_saver import ElasticsearchCheckpointSaver
        
        es = Elasticsearch("http://localhost:9200")
        checkpointer = ElasticsearchCheckpointSaver(es=es, index="my_checkpoints")
        ```
    """

    def __init__(self, es: Elasticsearch, index: str = "langgraph_checkpoints"):
        super().__init__()
        self.es = es
        self.index = index


    def _extract_configurable(self, config: RunnableConfig) -> dict:
        """
        Extract configurable dict from RunnableConfig safely.
        Handles ChainMap and nested structures.
        """
        configurable = config.get("configurable", {})
        # Convert ChainMap to regular dict
        if hasattr(configurable, 'maps'):
            # ChainMap - flatten it
            result = {}
            for m in reversed(configurable.maps):
                result.update(m)
            return result
        return dict(configurable)

    def _encode(self, data: tuple[str, bytes]) -> dict:
        return {
            "type": data[0],
            "blob": base64.b64encode(data[1]).decode()
        }

    def _decode(self, data: dict) -> tuple[str, bytes]:
        return (
            data["type"],
            base64.b64decode(data["blob"].encode())
        )
    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """
        Lấy checkpoint tuple từ Elasticsearch
        
        Args:
            config: RunnableConfig chứa thread_id và checkpoint_id
            
        Returns:
            CheckpointTuple nếu tìm thấy, None nếu không
        """
        try:
            configurable = self._extract_configurable(config)
            thread_id = configurable.get("thread_id")
            checkpoint_id = configurable.get("checkpoint_id")

            if not thread_id:
                logger.warning("No thread_id in config")
                return None

            # Nếu có checkpoint_id cụ thể, lấy checkpoint đó
            if checkpoint_id:
                doc_id = f"{thread_id}::{checkpoint_id}"
                try:
                    result = self.es.get(index=self.index, id=doc_id)
                    doc = result["_source"]
                    return self._doc_to_checkpoint_tuple(doc)
                except Exception as e:
                    logger.debug(f"Checkpoint {doc_id} not found: {e}")
                    return None

            # Nếu không có checkpoint_id, lấy checkpoint mới nhất
            query = {
                "query": {
                    "term": {"thread_id": thread_id}
                },
                "sort": [{"ts": {"order": "desc"}}],
                "size": 1
            }

            result = self.es.search(index=self.index, body=query)
            
            if result["hits"]["total"]["value"] == 0:
                return None

            doc = result["hits"]["hits"][0]["_source"]
            return self._doc_to_checkpoint_tuple(doc)

        except Exception as e:
            logger.error(f"Error getting checkpoint: {e}")
            return None

    def _doc_to_checkpoint_tuple(self, doc: dict) -> CheckpointTuple:
        """Convert Elasticsearch document to CheckpointTuple"""
        # Deserialize checkpoint data
        checkpoint =doc["checkpoint"]
        checkpoint = self.serde.loads_typed(self._decode(checkpoint))
      
        # Deserialize metadata
        metadata = doc["metadata"]
        metadata = self.serde.loads_typed(self._decode(metadata))
        
        # Handle parent_config
        parent_config = None
        if doc.get("parent_config"):
            parent_config = {
                "configurable": {
                    "thread_id": doc["thread_id"],
                    "checkpoint_id": doc["parent_config"]
                }
            }

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": doc["thread_id"],
                    "checkpoint_id": doc["checkpoint_id"],
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=None,
        )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """
        List các checkpoint theo điều kiện
        
        Args:
            config: Config chứa thread_id để filter
            filter: Điều kiện filter metadata bổ sung
            before: Chỉ lấy checkpoint trước config này
            limit: Giới hạn số lượng kết quả
            
        Yields:
            CheckpointTuple matching criteria
        """
        try:
            must_conditions = []

            # Filter by thread_id
            if config:
                configurable = self._extract_configurable(config)
                thread_id = configurable.get("thread_id")
                if thread_id:
                    must_conditions.append({"term": {"thread_id": thread_id}})

            # Filter by metadata - not implemented in this simple version
            # You can enhance this based on your needs

            # Filter by timestamp if 'before' is specified
            if before:
                before_configurable = self._extract_configurable(before)
                before_checkpoint_id = before_configurable.get("checkpoint_id")
                if before_checkpoint_id:
                    must_conditions.append({
                        "range": {"checkpoint_id": {"lt": before_checkpoint_id}}
                    })

            query = {
                "query": {"bool": {"must": must_conditions}} if must_conditions else {"match_all": {}},
                "sort": [{"ts": {"order": "desc"}}],
                "size": limit if limit else 10000
            }

            result = self.es.search(index=self.index, body=query)

            for hit in result["hits"]["hits"]:
                doc = hit["_source"]
                yield self._doc_to_checkpoint_tuple(doc)

        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
            return

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """
        Lưu checkpoint vào Elasticsearch
        
        Args:
            config: Config chứa thread_id
            checkpoint: Checkpoint data
            metadata: Metadata của checkpoint
            new_versions: Channel versions mới
            
        Returns:
            RunnableConfig đã cập nhật với checkpoint_id mới
        """
        try:
            configurable = self._extract_configurable(config)
            thread_id = configurable.get("thread_id")
            
            if not thread_id:
                raise ValueError("thread_id is required in config")


            # Use checkpoint's ID if available, otherwise generate new one
            checkpoint_id = checkpoint.get("id") if isinstance(checkpoint, dict) else str(checkpoint.get("id", self.get_next_version(None, None)))
            
            # Serialize checkpoint and metadata to bytes first, then to base64
            checkpoint = self.serde.dumps_typed(checkpoint)
            metadata = self.serde.dumps_typed(metadata)
            
            # Get parent checkpoint_id if exists
            parent_checkpoint_id = configurable.get("checkpoint_id")

            doc = {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "ts": datetime.utcnow().isoformat(),
                "checkpoint":self._encode(checkpoint),
                "metadata": self._encode(metadata),
                "parent_config": parent_checkpoint_id
            }

            doc_id = f"{thread_id}::{checkpoint_id}"
            self.es.index(index=self.index, id=doc_id, document=doc, refresh=True)

            logger.debug(f"Saved checkpoint {doc_id}")

            return {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id,
                }
            }

        except Exception as e:
            logger.error(f"Error putting checkpoint: {e}", exc_info=True)
            raise

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """
        Lưu intermediate writes vào Elasticsearch
        
        Args:
            config: Config của checkpoint liên quan
            writes: List các write operations
            task_id: ID của task
            task_path: Path của task
        """
        try:
            configurable = self._extract_configurable(config)
            thread_id = configurable.get("thread_id")
            checkpoint_id = configurable.get("checkpoint_id", "latest")

            if not thread_id:
                logger.warning("No thread_id in config for put_writes")
                return

            # Serialize writes to bytes
            writes = self.serde.dumps_typed(writes)

            doc = {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "task_path": task_path,
                "writes": self._encode(writes),
                "ts": datetime.utcnow().isoformat(),
                "type": "writes"
            }

            doc_id = f"{thread_id}::{checkpoint_id}::writes::{task_id}"
            self.es.index(index=self.index, id=doc_id, document=doc, refresh=True)
            
            logger.debug(f"Saved writes for {doc_id}")

        except Exception as e:
            logger.error(f"Error putting writes: {e}", exc_info=True)
            # Don't raise - writes are optional

    def delete_thread(self, thread_id: str) -> None:
        """
        Xóa tất cả checkpoint và writes của một thread
        
        Args:
            thread_id: ID của thread cần xóa
        """
        try:
            query = {"query": {"term": {"thread_id": thread_id}}}
            self.es.delete_by_query(index=self.index, body=query, refresh=True)
            logger.info(f"Deleted all checkpoints for thread: {thread_id}")

        except Exception as e:
            logger.error(f"Error deleting thread: {e}")
            raise

    # ==================== ASYNC METHODS ====================

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Async version of get_tuple"""
        return self.get_tuple(config)

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """Async version of list"""
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Async version of put"""
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Async version of put_writes"""
        self.put_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        """Async version of delete_thread"""
        self.delete_thread(thread_id)