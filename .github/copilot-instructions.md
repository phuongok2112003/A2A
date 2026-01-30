## Quick context

This repository implements an "agent-of-agents" system (A2A). Core pieces:

- `agent.py` — the central AgentCustom implementation and the project-wide SYSTEM_PROMPT. It wires LLMs, tools, dispatcher logic and streaming (`astream`).
- `Agent_Server/`, `Agent_Server_1/`, `Agent_Server_2/` — example agent executors and server-side entry points. Executors produce task-based streaming events using the A2A Task/TaskStatus model.
- `Agent_Client/` — client helpers used to call other agents (e.g. `create_client_for_agent`, `send_to_server_agent`).
- `services/chat_service.py` — shows how a higher-level service instantiates `AgentCustom` and calls it.
- `memory/` — memory backends: `PineconeMemoryStore` and Elasticsearch checkpoint saver are used for long-term memory.
- `config/settings.py` — environment variables and defaults (API keys, paths, base URLs).

## Big picture / data flow (short)

1. External request → server code creates a Task/ServerAgentRequest and enqueues it.
2. An Agent Executor (in `Agent_Server*`) runs and uses `AgentCustom` (from `agent.py`).
3. `AgentCustom` compiles a state graph and runs it with `astream`, producing incremental messages, interrupts (HITL) or a final AI message.
4. For cross-agent calls the `call_external_agent` StructuredTool is used. It delegates to `Agent_Client` to contact other agent servers.
5. Long-term memory reads/writes go to `memory/` backends (Pinecone or Elasticsearch) via the project's MemoryStore and saver classes.

## Developer workflows & commands

- Run the main app (used by other agents/tests):

  uvicorn main:app --host 0.0.0.0 --port 10000 --reload

- Elasticsearch index used for checkpoints: `langgraph_checkpoints`. README includes curl examples to delete it when needed.

- Environment variables are set via `.env` or the environment. See `config/settings.py` for the full list (e.g. `BASE_URL`, `AGENT_1_PATH`, `ELASTICSEARCH_URL`, `PINECONE_KEY`, `MODEL_EMBEDING`).

## Project-specific conventions to follow

- Message / task shapes: this project uses custom types from `a2a.types` and `schemas.base`.
  - `Message` contains `parts` which are `DataPart`, `TextPart` or `FilePart` (see `agent.py` for construction example).
  - Executors must send TaskStatusUpdateEvent with `final=True` for completion (see `Agent_Server_1/CurrencyAgentExecutor`).

- Streaming pattern: prefer `agent.astream(..., stream_mode=["values","updates","messages"])` and handle:
  - interrupt events (HITL) → send TaskState.input_required and wait for input
  - values/messages → collect final AIMessage for completion

- Cross-agent calls: use the `call_external_agent` StructuredTool produced by `AgentCustom._create_dispatcher_tool()`; input schema is `DispatcherInput` (fields: `agent_name`, `query`, optional `extra_data`, `file_path`). Example: `call_external_agent(agent_name="X", query="...", extra_data={...})`.

- File attachments: agents expect a `file_path` pointing to a local path on the called agent server. `AgentCustom` encodes files as base64 and wraps them in `FilePart`.

## Integration points & external deps

- LLMs: Google GenAI (`langchain_google_genai.ChatGoogleGenerativeAI`) and OpenAI-compatible local API (`ChatOpenAI` with `OPENAI_A2A_API_KEY` and `openai_api_base` pointing to local proxy).
- Vector stores: Pinecone (see `memory/PineconeMemoryStore`) and a checkpoint saver to Elasticsearch (`memory/elasticsearch_saver.py`).
- Networking: internal agent-to-agent calls use `Agent_Client` utilities; public endpoints and mount points are assembled using `BASE_URL + AGENT_1_PATH` etc.

## Quick examples found in-repo (copy/paste as starting templates)

- Creating AgentCustom with remote agents:

  access_agent_urls = [settings.BASE_URL + settings.AGENT_1_PATH, settings.BASE_URL + settings.AGENT_2_PATH]
  agent = await AgentCustom.create(access_agent_urls=access_agent_urls, tools=tools)

- Constructing dispatcher input (see `DispatcherInput` in `agent.py`):

  {
    "agent_name": "AgentNameFromRegistry",
    "query": "Explain the deployment steps",
    "extra_data": {"project": "X"}
  }

## Where to look for behavior you may need to change

- System prompt and tool discipline: `agent.py` contains the SYSTEM_PROMPT that shapes agent behavior. Edit with care.
- Task/event protocol: inspect `a2a.server.tasks`, `Agent_Server*/agent_executor.py` and `a2a.types` for event shapes and queue semantics.
- Memory & embeddings: change `settings.MODEL_EMBEDING` in env or `config/settings.py` to swap embedding model, and review `memory/PineconeMemoryStore`.

## Short checklist for PR authors / code edits

- Update `config/settings.py` or `.env` when adding third-party keys or endpoints.
- When changing streaming behaviour, add or update executor tests that assert `TaskStatusUpdateEvent.final==True` on completion.
- Keep `call_external_agent` input schema stable; changing it requires coordinating callers and the dispatcher generator.

---

If anything is missing or unclear here, tell me which area you want expanded (architecture, examples, or local run/debug steps) and I will iterate. 
