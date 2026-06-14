from __future__ import annotations

import os
import sys

from elasticsearch import Elasticsearch
from elasticsearch import ApiError
from elasticsearch import ConnectionError as ElasticsearchConnectionError


def create_client() -> Elasticsearch:
   

    return Elasticsearch(
        hosts=[
        "https://59587f037337424c96f573330a1ea05b.us-central1.gcp.cloud.es.io:443"
    ],
        api_key="ZFBzSnRwNEJEdzBvS3plVVBYaVM6QzhDMlp4U285WFZGR0ZfcVpDQk53QQ==",
        request_timeout=30,
        retry_on_timeout=True,
        max_retries=3,
    )


def main() -> int:
    try:
        client = create_client()

        print("=" * 60)
        print("Checking Elasticsearch Cloud connection...")
        print("=" * 60)

        info = client.info()

        print("\n[SUCCESS] Connected to Elasticsearch Cloud\n")

        print(f"Cluster Name : {info.get('cluster_name')}")
        print(f"Cluster UUID : {info.get('cluster_uuid')}")

        version = info.get("version", {})
        print(f"Version      : {version.get('number')}")

        health = client.cluster.health()

        print(f"Status       : {health.get('status')}")
        print(f"Nodes        : {health.get('number_of_nodes')}")
        print(f"Data Nodes   : {health.get('number_of_data_nodes')}")

        print("\nConnection test passed.")
        return 0

    except ValueError as exc:
        print(f"\n[CONFIG ERROR] {exc}")
        return 1

    except ElasticsearchConnectionError as exc:
        print(f"\n[CONNECTION ERROR] {exc}")
        return 2

    except ApiError as exc:
        print(
            f"\n[API ERROR] status={exc.status_code} "
            f"message={exc.message}"
        )
        return 3

    except Exception as exc:
        print(f"\n[UNEXPECTED ERROR] {type(exc).__name__}: {exc}")
        return 99


if __name__ == "__main__":
    sys.exit(main())