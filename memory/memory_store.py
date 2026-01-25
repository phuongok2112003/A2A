from __future__ import annotations

import json
import uuid
import contextlib
from typing import Iterable, Any
from langgraph.store.memory import InMemoryStore
from pinecone import Pinecone
from config.settings import settings
from langgraph.store.base import (
    BaseStore,
    GetOp,
    Item,
    ListNamespacesOp,
    Op,
    PutOp,
    Result,
    SearchItem,
    SearchOp,
)

from langchain_pinecone import PineconeEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

# ---------------------------
# Helpers
# ---------------------------

def ns_tuple_to_str(ns: tuple[str, ...]) -> str:
    return "/".join(ns)

def _clean_metadata_for_pinecone(metadata: dict) -> dict:
    """
    Làm sạch metadata để tuân thủ luật của Pinecone:
    - Chỉ chấp nhận: String, Number, Boolean, List[String].
    - Không chấp nhận: Nested Dict, List[Int], None...
    """
    clean = {}
    for k, v in metadata.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif isinstance(v, list):
            # Ép kiểu thành list of strings
            clean[k] = [str(item) for item in v]
        elif isinstance(v, dict):
            # Ép nested dict thành string JSON
            clean[f"{k}_json"] = json.dumps(v, ensure_ascii=False)
        else:
            clean[k] = str(v)
    return clean

# ---------------------------
# Pinecone-backed Store
# ---------------------------

class PineconeMemoryStore(BaseStore):
    supports_ttl = False

    def __init__(
        self,
        *,
        api_key: str,
        index_name: str = "langgraph-store",
    ):
        self.pc = Pinecone(api_key=api_key)
        
        # Logic tạo index (giữ nguyên logic của bạn)
        if not self.pc.has_index(index_name):
            self.pc.create_index_for_model(
                name=index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": settings.MODEL_EMBEDING,
                    "field_map": {"text": "text"}
                }
            )
        self.index = self.pc.Index(index_name)

        self.embeddings = PineconeEmbeddings(model=settings.MODEL_EMBEDING, pinecone_api_key=settings.PINECONE_KEY)
        self.vector_store  = PineconeVectorStore(index=self.index, embedding=self.embeddings)

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        raise RuntimeError("Use async APIs (abatch)")

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        results: list[Result] = []
        for op in ops:
            if isinstance(op, GetOp):
                results.append(await self._get(op))
            elif isinstance(op, PutOp):
                results.append(await self._put(op))
            elif isinstance(op, SearchOp):
                results.append(await self._search(op))
            elif isinstance(op, ListNamespacesOp):
                results.append(await self._list_namespaces(op))
            else:
                raise NotImplementedError(type(op))
        return results

    # ------------------------
    # Operations
    # ------------------------

    async def _get(self, op: GetOp):
        namespace = ns_tuple_to_str(op.namespace)
        res = self.index.fetch(ids=[op.key], namespace=namespace)

        if not res.vectors or op.key not in res.vectors:
            return None

        vec = res.vectors[op.key]
        return Item(
            key=op.key,
            namespace=op.namespace,
            value=vec.metadata, # Pinecone integrated trả về metadata chứa cả text gốc
        )

    async def _put(self, op: PutOp):
        namespace = ns_tuple_to_str(op.namespace)

        if op.value is None:
            self.index.delete(ids=[op.key], namespace=namespace)
            return None

      
        raw_metadata = op.value.get("metadata", {})

        documment =Document(
            id= op.key,
            page_content=op.value.get("text",""),
            metadata=raw_metadata,
        )
        await self.vector_store.aadd_documents([documment])

        return None

    async def _search(self, op: SearchOp):
        namespace = ns_tuple_to_str(op.namespace_prefix)

        query_payload = {
            "inputs": {
                "text": op.query
            },
            "top_k": op.limit
        }

        results = await self.vector_store.asimilarity_search_with_score(
            op.query,
            k=op.limit,
            filter=op.filter,
        )

        items: list[SearchItem] = []


        for res, score in results:
   

            items.append(
                SearchItem(
                    namespace=op.namespace_prefix,
                    created_at=res.metadata["created_at"],
                    updated_at= res.metadata["created_at"],
                    key=res.id,
                    value=res.page_content,
                    score=score,
                )
            )

        return items


    async def _list_namespaces(self, op: ListNamespacesOp):
        raise NotImplementedError("Pinecone does not support listing namespaces.")