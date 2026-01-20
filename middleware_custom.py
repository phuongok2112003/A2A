from typing import Any, Dict, Callable, Awaitable
from langchain.agents.middleware import AgentMiddleware
from langgraph.types import StateSnapshot, Command
from langchain_core.messages import ToolMessage, AIMessage
import logging
import time
from config.settings import settings

logger = logging.getLogger(__name__)


class MiddlewareCustom(AgentMiddleware):
    """
    Custom middleware implement đầy đủ các method của AgentMiddleware
    
    Lifecycle:
    1. before_agent()      - Chạy khi agent bắt đầu
    2. before_model()      - Chạy trước mỗi lần gọi model
    3. wrap_model_call()   - Bao bọc việc gọi model
    4. after_model()       - Chạy sau mỗi lần gọi model
    5. wrap_tool_call()    - Bao bọc việc gọi tool
    6. after_agent()       - Chạy khi agent kết thúc
    """
    
    def __init__(self, enable_logging: bool = True):
        """
        Args:
            enable_logging: Bật/tắt logging chi tiết
        """
        super().__init__()
        self.enable_logging = enable_logging
        self.stats = {
            "agent_runs": 0,
            "model_calls": 0,
            "tool_calls": 0,
            "total_time": 0.0
        }
    
    @property
    def name(self) -> str:
        """Tên của middleware"""
        return "MiddlewareCustom"
    
    # ==================== AGENT LIFECYCLE ====================
    
    def before_agent(self, state, runtime) -> Dict[str, Any] | None:
        """
        Chạy TRƯỚC KHI agent bắt đầu execution
        
        Use cases:
        - Initialize resources
        - Validate input state
        - Add system prompts
        - Setup context
        """
        self.stats["agent_runs"] += 1
        self._log(f"🚀 Agent starting (run #{self.stats['agent_runs']})")

        print(f"\n\nbefore_agent --------- State: {state}\n Runtime: {runtime}")
        
        # Ví dụ: Thêm timestamp vào state
        self.start_time = time.time()
        
        # Có thể modify state bằng cách return dict
        # return {"custom_field": "some_value"}
        
        return None
    
    async def abefore_agent(self, state, runtime) -> Dict[str, Any] | None:
        """Async version của before_agent"""
        # Có thể có logic async ở đây (gọi API, database, etc.)
        return self.before_agent(state, runtime)
    
    def after_agent(self, state, runtime) -> Dict[str, Any] | None:
        """
        Chạy SAU KHI agent hoàn thành execution
        
        Use cases:
        - Cleanup resources
        - Log final results
        - Save metrics
        - Post-processing
        """
        elapsed = time.time() - self.start_time
        self.stats["total_time"] += elapsed
        
        self._log(f"✅ Agent completed in {elapsed:.2f}s")
        self._log(f"📊 Stats: {self.stats}")
        print(f"\n\nafter_agent --------- State: {state}\n Runtime: {runtime}")
        return None
    
    async def aafter_agent(self, state, runtime) -> Dict[str, Any] | None:
        """Async version của after_agent"""
        return self.after_agent(state, runtime)
    
    # ==================== MODEL LIFECYCLE ====================
    
    def before_model(self, state, runtime) -> Dict[str, Any] | None:
        """
        Chạy TRƯỚC KHI gọi model
        
        Use cases:
        - Validate messages
        - Add context to messages
        - Log input
        - Modify state before model sees it
        """
        self.stats["model_calls"] += 1
        
        messages = state.get("messages", [])
        self._log(f"📝 Before model call #{self.stats['model_calls']} - {len(messages)} messages")
        
        # Ví dụ: Log message cuối cùng
        if messages:
            last_msg = messages[-1]
            self._log(f"   Last message: {type(last_msg).__name__}")
        
        # Có thể modify state
        # return {"messages": modified_messages}
        print(f"\n\nbefore_model --------- State: {state}\n Runtime: {runtime}")
        return None
    
    async def abefore_model(self, state, runtime) -> Dict[str, Any] | None:
        """Async version của before_model"""
        return self.before_model(state, runtime)
    
    def after_model(self, state, runtime) -> Dict[str, Any] | None:
        """
        Chạy SAU KHI model trả về response
        
        Use cases:
        - Log model output
        - Validate response
        - Post-process response
        - Extract metadata
        """
        messages = state.get("messages", [])
        
        if messages:
            last_msg = messages[-1]
            self._log(f"🤖 After model - Response type: {type(last_msg).__name__}")
            
            # Log nếu là AIMessage
            if isinstance(last_msg, AIMessage):
                content_preview = str(last_msg.content)[:100]
                self._log(f"   Content preview: {content_preview}...")
        print(f"\n\nafter_model --------- State: {state}\n Runtime: {runtime}")
        return None
    
    async def aafter_model(self, state, runtime) -> Dict[str, Any] | None:
        """Async version của after_model"""
        return self.after_model(state, runtime)
    
    # ==================== MODEL CALL WRAPPER ====================
    
    def wrap_model_call(self, request, handler: Callable) -> Any:
        """
        BÃO BỌC việc gọi model - Có quyền kiểm soát hoàn toàn
        
        Use cases:
        - Retry on error
        - Cache responses
        - Modify request/response
        - Measure performance
        - Short-circuit execution
        
        Args:
            request: ModelRequest chứa state và runtime
            handler: Callback để thực thi model call
            
        Returns:
            ModelResponse hoặc AIMessage
        """
        start = time.time()
        
        try:
            self._log(f"⚡ Wrapping model call...")
            
            # Ví dụ 1: Đơn giản - chỉ gọi handler
            # response = handler(request)
            
            # Ví dụ 2: Retry logic
            response = self._retry_model_call(request, handler, max_retries=3)
            
            elapsed = time.time() - start
            self._log(f"⚡ Model call completed in {elapsed:.2f}s")
            print(f"\n\nwrap_model_call --------- Request: {request}\n Handler: {handler}")
            return response
            
        except Exception as e:
            self._log(f"❌ Model call error: {e}")
            raise
    
    def _retry_model_call(self, request, handler, max_retries: int = 3):
        """Helper: Retry logic cho model call"""
        for attempt in range(max_retries):
            try:
                response = handler(request)
                
                # Validate response
                if self._is_valid_response(response):
                    return response
                    
                self._log(f"⚠️ Invalid response, retry {attempt + 1}/{max_retries}")
                
            except Exception as e:
                if attempt == max_retries - 1:
                    self._log(f"❌ All retries failed")
                    raise
                    
                self._log(f"⚠️ Attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
      
        return response
    
    def _is_valid_response(self, response) -> bool:
        """Validate model response"""
        # Implement validation logic
        return True
    
    async def awrap_model_call(
        self, 
        request, 
        handler: Callable[[Any], Awaitable[Any]]
    ) -> Any:
        """
        Async version của wrap_model_call
        """
        start = time.time()
        
        try:
            self._log(f"⚡ Wrapping async model call...")
            
            # Async retry logic
            response = await self._async_retry_model_call(request, handler, max_retries=3)
            
            elapsed = time.time() - start
            self._log(f"⚡ Async model call completed in {elapsed:.2f}s")
            
            return response
            
        except Exception as e:
            self._log(f"❌ Async model call error: {e}")
            raise
    
    async def _async_retry_model_call(self, request, handler, max_retries: int = 3):
        """Helper: Async retry logic"""
        import asyncio
        
        for attempt in range(max_retries):
            try:
                response = await handler(request)
                
                if self._is_valid_response(response):
                    return response
                    
                self._log(f"⚠️ Invalid async response, retry {attempt + 1}/{max_retries}")
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                    
                self._log(f"⚠️ Async attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
        
        return response
    
    # ==================== TOOL CALL WRAPPER ====================
    
    def wrap_tool_call(self, request, handler: Callable) -> ToolMessage | Command:
        """
        BÃO BỌC việc gọi tool - Kiểm soát tool execution
        
        Use cases:
        - Retry on tool errors
        - Validate tool inputs
        - Modify tool arguments
        - Cache tool results
        - Monitor tool usage
        
        Args:
            request: ToolCallRequest với tool_call dict, BaseTool, state, runtime
            handler: Callback để thực thi tool
            
        Returns:
            ToolMessage hoặc Command
        """
        self.stats["tool_calls"] += 1
        
        tool_name = request.tool_call.get("name", "unknown")
        tool_args = request.tool_call.get("args", {})
        
        self._log(f"🔧 Tool call #{self.stats['tool_calls']}: {tool_name}")
        self._log(f"   Args: {tool_args}")
        
        try:
            # Ví dụ 1: Đơn giản - chỉ gọi handler
            # result = handler(request)
            
            # Ví dụ 2: Retry với validation
            result = self._retry_tool_call(request, handler, max_retries=3)
            
            self._log(f"✅ Tool {tool_name} completed successfully")
            print(f"\n\nwrap_tool_call --------- Request: {request}\n Handler: {handler}")
            return result
            
        except Exception as e:
            self._log(f"❌ Tool {tool_name} error: {e}")
            raise
    
    def _retry_tool_call(self, request, handler, max_retries: int = 3):
        """Helper: Retry logic cho tool call"""
        for attempt in range(max_retries):
            try:
                result = handler(request)
                
                # Validate result
                if isinstance(result, ToolMessage):
                    if result.status != "error":
                        return result
                    
                    self._log(f"⚠️ Tool returned error status, retry {attempt + 1}/{max_retries}")
                else:
                    # Command or other result
                    return result
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                    
                self._log(f"⚠️ Tool attempt {attempt + 1} failed: {e}")
                time.sleep(0.3 * (attempt + 1))
        
        return result
    
    async def awrap_tool_call(
        self, 
        request, 
        handler: Callable[[Any], Awaitable[ToolMessage | Command]]
    ) -> ToolMessage | Command:
        """
        Async version của wrap_tool_call
        """
        self.stats["tool_calls"] += 1
        
        tool_name = request.tool_call.get("name", "unknown")
        
        self._log(f"🔧 Async tool call #{self.stats['tool_calls']}: {tool_name}")
        
        try:
            result = await self._async_retry_tool_call(request, handler, max_retries=3)
            
            self._log(f"✅ Async tool {tool_name} completed")
            
            return result
            
        except Exception as e:
            self._log(f"❌ Async tool {tool_name} error: {e}")
            raise
    
    async def _async_retry_tool_call(self, request, handler, max_retries: int = 3):
        """Helper: Async retry logic cho tool"""
        import asyncio
        
        for attempt in range(max_retries):
            try:
                result = await handler(request)
                
                if isinstance(result, ToolMessage) and result.status != "error":
                    return result
                elif not isinstance(result, ToolMessage):
                    return result
                    
                self._log(f"⚠️ Async tool error status, retry {attempt + 1}/{max_retries}")
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                    
                await asyncio.sleep(0.3 * (attempt + 1))
        
        return result
    
    # ==================== HELPER METHODS ====================
    
    def _log(self, message: str):
        """Helper để log với format đẹp"""
        if self.enable_logging:
            logger.info(f"[{self.name}] {message}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset thống kê"""
        self.stats = {
            "agent_runs": 0,
            "model_calls": 0,
            "tool_calls": 0,
            "total_time": 0.0
        }

