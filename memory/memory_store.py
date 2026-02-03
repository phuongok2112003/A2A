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
        print("=======================Nhay vào batch--===============================")
        results = []
        for op in ops:
            if isinstance(op, GetOp):
                print("\n\nGọi vào get====\n\n")
                results.append(self._get_sync(op))
            elif isinstance(op, PutOp):
                print("\n\nGọi vào put====\n\n")
                results.append(self._put_sync(op))
            elif isinstance(op, SearchOp):
                print("\n\nGọi vào search====\n\n")
                results.append(self._search_sync(op))
        return results
    


    def _get_sync(self, op: GetOp) -> Optional[Item]:
        namespace = ns_tuple_to_str(op.namespace)
        res = self.index.fetch(ids=[op.key], namespace=namespace)
       
        if op.key not in res.vectors:
            return None
            
        vec = res.vectors[op.key]
        content = vec.metadata.get("text") or vec.metadata.get("page_content")

        if not content:
            raise ValueError("Missing content in Pinecone metadata")

        return Item(
            key=op.key,
            value={  
                "content": content,
                "created_at": vec.metadata.get("created_at"),
                "updated_at": vec.metadata.get("updated_at")
            },
            namespace=op.namespace,
            created_at=vec.metadata.get("created_at"),
            updated_at=vec.metadata.get("updated_at"),
        )
   
    def _put_sync(self, op: PutOp) -> Optional[Result]:
        namespace = ns_tuple_to_str(op.namespace)
        
        if op.value is None:
            self.index.delete(ids=[op.key], namespace=namespace)
            return None

       
        text =  json.dumps(op.value)

        print(f"\n\nText trong put {text}\n\n")

        
        doc = Document(
            id=op.key,
            page_content=str(op.value.get("content")),
            metadata={
                "text": str(op.value.get("content")),
                "namespace": namespace,  # Để filter
                "created_at": op.value.get("created_at", datetime.now().isoformat()),
                "updated_at": op.value.get("updated_at", datetime.now().isoformat())
            }
        )
        

        self.vector_store.add_documents([doc], ids=[op.key], namespace=namespace)
        return None

    def _search_sync(self, op: SearchOp) -> List[SearchItem]:
        print(f"data in search {op}")
        if not op.query:
            return []
        filter_dict = op.filter or {}
        if op.namespace_prefix:
            filter_dict["namespace"] = {"$like": f"{ns_tuple_to_str(op.namespace_prefix)}%"}

        results = self.vector_store.similarity_search_with_score(
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
                    "content": doc.page_content,
                    "metadata": doc.metadata
                },
                score=float(score),
                created_at=doc.metadata.get("created_at"),
                updated_at=doc.metadata.get("updated_at")
            ))
        return items



    async def abatch(self, ops: Iterable[Op]) -> List[Result]:
        print("=======================Nhay vào abatch--===============================")
        results = []
        for op in ops:
            if isinstance(op, GetOp):
                print("\n\nGọi vào _aget====\n\n")
                results.append(await self._aget(op))
            elif isinstance(op, PutOp):
                print("\n\nGọi vào _aput====\n\n")
                results.append(await self._aput(op))
            elif isinstance(op, SearchOp):
                print("\n\nGọi vào _asearch====\n\n")
                results.append(await self._asearch(op))
            elif isinstance(op, ListNamespacesOp):
                print("\n\nGọi vào _alist_namespaces====\n\n")
                results.append(await self._alist_namespaces(op))
        return results

  
    async def _aget(self, op: GetOp) -> Optional[Item]:
        namespace = ns_tuple_to_str(op.namespace)
        res = self.index.fetch(ids=[op.key], namespace=namespace)
    
        if op.key not in res.vectors:
            return None
            
        vec = res.vectors[op.key]
        content = vec.metadata.get("text") or vec.metadata.get("page_content")

        if not content:
            raise ValueError("Missing content in Pinecone metadata")

     
        return Item(
            key=op.key,
            value={  # ← Thay vì `value=content`
                "content": content,
                "created_at": vec.metadata.get("created_at"),
                "updated_at": vec.metadata.get("updated_at")
            },
            namespace=op.namespace,
            created_at=vec.metadata.get("created_at"),
            updated_at=vec.metadata.get("updated_at"),
        )

   
    async def _aput(self, op: PutOp) -> Optional[Result]:
        namespace = ns_tuple_to_str(op.namespace)
        
        if op.value is None:
            self.index.delete(ids=[op.key], namespace=namespace)
            return None

       
        text =  json.dumps(op.value)


        print(f"\n\nText trong put {text}\n\n")

        doc = Document(
            id=op.key,
            page_content=str(op.value.get("content")),
            metadata={
                "text": str(op.value.get("content")),
                "namespace": namespace,  # Để filter
                "created_at": op.value.get("created_at", datetime.now().isoformat()),
                "updated_at": op.value.get("updated_at", datetime.now().isoformat())
            }
        )
        

        await self.vector_store.aadd_documents([doc], ids=[op.key], namespace=namespace)
        return None

    async def _asearch(self, op: SearchOp) -> List[SearchItem]:
        print(f"data in search {op}")
        if not op.query:
            op.query = ""
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
                    "content": doc.page_content,
                    "metadata": doc.metadata
                },
                score=float(score),
                created_at=doc.metadata.get("created_at"),
                updated_at=doc.metadata.get("updated_at")
            ))
        return items

     
    async def _alist_namespaces(self, op: ListNamespacesOp) -> List[str]:
      
        return []
        
       

