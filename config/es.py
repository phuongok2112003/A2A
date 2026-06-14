from elasticsearch import Elasticsearch
from config.settings import settings
def init_elasticsearch_sync(index_elastic)->Elasticsearch:
  es = Elasticsearch(
        hosts=[
        "https://59587f037337424c96f573330a1ea05b.us-central1.gcp.cloud.es.io:443"
    ],
        api_key="ZFBzSnRwNEJEdzBvS3plVVBYaVM6QzhDMlp4U285WFZGR0ZfcVpDQk53QQ==",
        request_timeout=30,
        retry_on_timeout=True,
        max_retries=3,
    )

  try:
      if not es.indices.exists(index=index_elastic):
          es.indices.create(
              index=index_elastic,
              timeout="30s",
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