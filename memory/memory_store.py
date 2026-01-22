from __future__ import annotations

import json
from typing import Iterable

from pinecone import Pinecone

from langgraph.store.base import (
    BaseStore,
    GetOp,
    Item,
    ListNamespacesOp,
    MatchCondition,
    Op,
    PutOp,
    Result,
    SearchItem,
    SearchOp,
)

# ---------------------------
# Helpers
# ---------------------------

def ns_tuple_to_str(ns: tuple[str, ...]) -> str:
    return "/".join(ns)


# ---------------------------
# Pinecone-backed Store
# ---------------------------

class PineconeMemoryStore(BaseStore):
    """
    LangGraph long-term memory backed by Pinecone vector DB.

    Uses Pinecone integrated embedding model (llama-text-embed-v2).
    """

    supports_ttl = False

    def __init__(
        self,
        *,
        api_key: str,
        index_name: str= "langgraph-store",
    ):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    # ------------------------
    # Batch API
    # ------------------------

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        raise RuntimeError("Use async APIs (abatch)")

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        results: list[Result] = []
        
        print(f"\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++Chạy vào store rồi ne++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n")
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

        res = self.index.fetch(
            ids=[op.key],
            namespace=namespace,
        )

        if not res.vectors or op.key not in res.vectors:
            return None

        vec = res.vectors[op.key]

        return Item(
            key=op.key,
            namespace=op.namespace,
            value=vec.metadata,
        )

    async def _put(self, op: PutOp):
        namespace = ns_tuple_to_str(op.namespace)

        # delete
        if op.value is None:
            self.index.delete(
                ids=[op.key],
                namespace=namespace,
            )
            return None

        # Pinecone integrated embedding:
        # field "text" will be embedded automatically
        record = {
            "id": op.key,
            "text": json.dumps(op.value, ensure_ascii=False),
            **op.value,
        }

        self.index.upsert(
            records=[record],
            namespace=namespace,
        )

        return None

    async def _search(self, op: SearchOp):
        namespace = ns_tuple_to_str(op.namespace_prefix)

        res = self.index.query(
            namespace=namespace,
            query=op.query,
            top_k=op.limit,
            include_metadata=True,
            filter=op.filter,
        )

        return [
            SearchItem(
                namespace=op.namespace_prefix,
                key=match["id"],
                value=match["metadata"],
                score=match["score"],
            )
            for match in res.matches
        ]

    async def _list_namespaces(self, op: ListNamespacesOp):
        # Pinecone currently cannot enumerate namespaces
        raise NotImplementedError(
            "Pinecone does not support listing namespaces programmatically."
        )
