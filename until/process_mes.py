from langgraph.types import Command  
import asyncio

async def async_input(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)

async def process_mess_interrupt(hitl_request: dict):
    action_requests = hitl_request["action_requests"]
 
    decisions = []
              
    for req in action_requests:
                        
        decision = (await async_input(
            "Decision (approve / reject / edit): "
        )).strip().lower()

        if decision == "approve":
            decisions.append({"type": "approve"})

        elif decision == "reject":
            message = await async_input("Reject reason: ")
            decisions.append({
                "type": "reject",
                "message": message
            })
        elif decision == "edit":
            new_args = {}
            for k, v in req["args"].items():
                new_args[k] = await async_input(
                    f"{k} (default={v}): "
                )

            decisions.append({
                "type": "edit",
                "edited_action": {
                    "name": req["name"],
                    "args": new_args
                }
            })
    
    return decisions