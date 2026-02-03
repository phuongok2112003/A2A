from __future__ import annotations
import json
from typing import Iterable, Any, List, Optional
from langgraph.store.base import BaseStore, GetOp, PutOp, SearchOp, ListNamespacesOp, Result, Item, SearchItem, Op
from langgraph.store.memory import InMemoryStore 
from pinecone import Pinecone
from config.settings import settings
from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from langchain_core.documents import Document
from datetime import datetime
import asyncio

def ns_tuple_to_str(ns: tuple[str, ...]) -> str:
    return "/".join(ns)

class PineconeMemoryStore(BaseStore):
    supports_ttl = False 

    def __init__(self, api_key: str, index_name: str = "langgraph-store"):
        self.pc = Pinecone(api_key=api_key)
        if index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=index_name,
                dimension=1536, 
                metric="cosine",
                pods=1
            )
        self.index = self.pc.Index(index_name)
        self.embeddings = PineconeEmbeddings(
            model=settings.MODEL_EMBEDING, 
            pinecone_api_key=api_key
        )
        self.vector_store = PineconeVectorStore(
            index=self.index, 
            embedding=self.embeddings
        )

    
    def batch(self, ops: Iterable[Op]) -> List[Result]:
        print("=======================Nhay vào ppicnjdfhu--===============================")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return loop.run_until_complete(self.abatch(ops))
        else:
            return asyncio.run(self.abatch(ops))

    async def abatch(self, ops: Iterable[Op]) -> List[Result]:
        results = []
        for op in ops:
            if isinstance(op, GetOp):
                results.append(await self._aget(op))
            elif isinstance(op, PutOp):
                results.append(await self._aput(op))
            elif isinstance(op, SearchOp):
                results.append(await self._asearch(op))
            elif isinstance(op, ListNamespacesOp):
                results.append(await self._alist_namespaces(op))
        return results

  
    async def _aget(self, op: GetOp) -> Optional[Item]:
        namespace = ns_tuple_to_str(op.namespace)
        res = self.index.fetch(ids=[op.key], namespace=namespace)
        print("REst ",res)
        if op.key not in res.vectors:
            return None
            
        vec = res.vectors[op.key]
        value = {
            "text": vec.metadata.get("text", ""),  # Nội dung gốc
            "metadata": vec.metadata
        }
        return Item(key=op.key, value=value, namespace=op.namespace,
                     updated_at=vec.metadata.get("updated_at", ""),created_at=vec.metadata.get("created_at", ""))

   
    async def _aput(self, op: PutOp) -> Optional[Result]:
        namespace = ns_tuple_to_str(op.namespace)
        
        if op.value is None:
            self.index.delete(ids=[op.key], namespace=namespace)
            return None

        # Chuẩn hóa value thành Document cho Pinecone
        text = op.value.get("text", json.dumps(op.value))
        metadata = op.value.get("metadata", {})
        
        doc = Document(
            id=op.key,
            page_content=text,
            metadata={
                **metadata,
                "namespace": namespace,  # Để filter
                "created_at": metadata.get("created_at", datetime.now().isoformat()),
                "updated_at": metadata.get("updated_at", datetime.now().isoformat())
            }
        )
        

        await self.vector_store.aadd_documents([doc], ids=[op.key], namespace=namespace)
        return None

    async def _asearch(self, op: SearchOp) -> List[SearchItem]:
     
        filter_dict = op.filter or {}
        if op.namespace_prefix:
            filter_dict["namespace"] = {"$like": f"{ns_tuple_to_str(op.namespace_prefix)}%"}

        results = await self.vector_store.asimilarity_search_with_score(
            query=op.query,
            k=op.limit or 4,
            filter=filter_dict
        )
        
        items = []
        for doc, score in results:
            items.append(SearchItem(
                namespace=op.namespace_prefix,
                 key=doc.id,
                value={
                    "text": doc.page_content,
                    "metadata": doc.metadata
                },
                score=float(score),
                created_at=doc.metadata.get("created_at"),
                updated_at=doc.metadata.get("updated_at")
            ))
        return items

     
    async def _alist_namespaces(self, op: ListNamespacesOp) -> List[str]:
      
        return []
        
       

