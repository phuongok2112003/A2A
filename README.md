curl -X DELETE "http://10.0.13.13:9201/langgraph_checkpoints?pretty"
uvicorn main:app --host 0.0.0.0 --port 10000 --reload

