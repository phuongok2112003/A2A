from typing import List, Dict, Any
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
def process_interrupt(decisions: List[Dict[str, Any]], agent : CompiledStateGraph , config : dict ) -> Command:

        decision_type = decisions[0].get('type') if decisions else 'approve'
        if decision_type == "approve":
            return Command(resume={"decisions": decisions})
        elif decision_type == "edit":
            # User chỉnh sửa → xóa state cũ, input lại
                    # Tạo message với command để agent biết tool nào sẽ được gọi

            edited_action = decisions[0].get('edited_action')
            tool_name = edited_action.get('name')
            tool_args = edited_action.get('args')

            print(f"📝 User edited action:")
            print(f"   Tool: {tool_name}")
            print(f"   New Args: {tool_args}")
            command_content = f"""Toi muốn chạy tool này với 
            [TOOL CALL COMMAND]
Tool: {tool_name}
Args: {tool_args}

Hãy thực thi tool này với các tham số đã sửa. 
***Có thể các tham số mới có thể thay thế ý định ban đầu của tôi nhưng hãy chạy tool này với tham só này***"""
            
            #agent.update_state(config=config, v)
            msg = (HumanMessage(
                content=[{"type": "text", "text": command_content}]
            ))
            agent.update_state(config=config, values={"messages": [msg]})
            # current_input = {"messages": new_messages}
        else:  # reject
            # Dừng lại, không tiếp tục
            reason = decisions[0].get('message')
            msg = (HumanMessage(
                content=[{"type": "text", "text": f"Tôi khong muốn chạy tool này nữa với lý do: {reason}"}]
            ))
            agent.update_state(config=config, values={"messages": [msg]})

        return Command(resume={"decisions": decisions})