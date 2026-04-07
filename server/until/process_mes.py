from langgraph.types import Command  
import asyncio
import threading
from until.hitl_dialog import HitlDialog
from typing import Dict, Any, List
async def async_input(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)

# async def process_mess_interrupt(hitl_request: dict):
#     action_requests = hitl_request["action_requests"]
 
#     decisions = []
              
#     for req in action_requests:
                        
#         decision = (await async_input(
#             "Decision (approve / reject / edit): "
#         )).strip().lower()

#         if decision == "approve":
#             decisions.append({"type": "approve"})

#         elif decision == "reject":
#             message = await async_input("Reject reason: ")
#             decisions.append({
#                 "type": "reject",
#                 "message": message
#             })
#         elif decision == "edit":
#             new_args = {}
#             for k, v in req["args"].items():
#                 new_args[k] = await async_input(
#                     f"{k} (default={v}): "
#                 )

#             decisions.append({
#                 "type": "edit",
#                 "edited_action": {
#                     "name": req["name"],
#                     "args": new_args
#                 }
#             })
    
#     return decisions

async def process_mess_interrupt(hitl_request: dict) -> List[Dict[str, Any]]:

    loop = asyncio.get_running_loop()
    future: asyncio.Future[List[Dict[str, Any]]] = loop.create_future()

    def run_ui():
        dialog = HitlDialog(hitl_request)
        result = dialog.show()
        loop.call_soon_threadsafe(future.set_result, result)

    threading.Thread(target=run_ui, daemon=True).start()

    return await future