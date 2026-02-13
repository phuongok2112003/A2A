from elasticsearch import Elasticsearch
from config.settings import settings
def init_elasticsearch_sync(index_elastic)->Elasticsearch:
  es = Elasticsearch(settings.ELASTICSEARCH_URL)

  try:
      if not es.indices.exists(index=index_elastic):
          es.indices.create(
              index=index_elastic,
              body={
                  "mappings": {
                      "properties": {
                          "thread_id": {"type": "keyword"},
                          "checkpoint_id": {"type": "keyword"},
                          "ts": {"type": "date"},
                          "parent_config": {"type": "keyword"},
                          "type": {"type": "keyword"},
                          # Object với nested structure
                          "checkpoint": {
                              "properties": {
                                  "type": {"type": "keyword"},
                                  "blob": {"type": "text", "index": False},
                              }
                          },
                          "metadata": {
                              "properties": {
                                  "type": {"type": "keyword"},
                                  "blob": {"type": "text", "index": False},
                              }
                          },
                          "writes": {
                              "properties": {
                                  "type": {"type": "keyword"},
                                  "blob": {"type": "text", "index": False},
                              }
                          },
                          # Các trường cho put_writes
                          "task_id": {"type": "keyword"},
                          "task_path": {"type": "keyword"},
                      }
                  }
              },
          )
      return es

  except Exception as e:
      raise ValueError(f"Elasticsearch connection error: {e}")