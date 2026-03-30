# import cv2
# from typing import Optional, List, Tuple
# import platform
# import os
# import subprocess


# def list_linux_cameras() -> List[Tuple[str, str]]:
#     """
#     Liệt kê camera trên Linux bằng v4l2-ctl hoặc fallback os.listdir.
#     Tránh mở VideoCapture nhiều lần → không trigger privacy portal popup lặp.
#     """
#     system = platform.system().lower()
#     if system != "linux":
#         return []

#     cameras = []
#     try:
#         # Ưu tiên v4l2-ctl nếu có (cài v4l-utils)
#         result = subprocess.run(
#             ["v4l2-ctl", "--list-devices"],
#             capture_output=True, text=True, check=False
#         )
#         if result.returncode == 0:
#             lines = result.stdout.splitlines()
#             current_name = ""
#             for line in lines:
#                 if line.strip() and not line.startswith("\t"):
#                     current_name = line.strip()
#                 elif "/dev/video" in line:
#                     dev_path = line.strip().split()[0]
#                     cameras.append((dev_path, current_name or "Unknown"))
#             return cameras

#     except FileNotFoundError:
#         # Không có v4l2-ctl → fallback đơn giản
#         pass

#     # Fallback: liệt kê /dev/video* (ít thông tin hơn)
#     for dev in sorted(os.listdir("/dev")):
#         if dev.startswith("video"):
#             path = f"/dev/{dev}"
#             name = "Integrated Webcam" if "0" in dev else f"USB Camera {dev}"
#             cameras.append((path, name))

#     return cameras


# def open_webcam(
#     camera_id: Optional[int | str] = None,
#     width: int = 1280,
#     height: int = 720,
#     fps: int = 30,
#     auto_detect: bool = False  # Mặc định False để tránh popup
# ) -> None:
#     """
#     Mở webcam cross-platform, ưu tiên tránh multiple VideoCapture calls trên Linux.
#     """
#     system = platform.system().lower()

#     if camera_id is None:
#         if system == "linux" and auto_detect:
#             cameras = list_linux_cameras()
#             if not cameras:
#                 raise RuntimeError("Không tìm thấy camera trên Linux.")
#             camera_id, desc = cameras[0]  # Chọn cái đầu tiên (thường /dev/video0)
#             print(f"Tự động chọn: {desc} → {camera_id}")
#         else:
#             camera_id = 0 if system != "linux" else "/dev/video0"

#     # Validate type
#     if not isinstance(camera_id, (int, str)):
#         raise ValueError("camera_id phải là int (index) hoặc str (device path)")

#     # Chọn backend
#     if system == "linux":
#         backend = cv2.CAP_V4L2
#     else:
#         backend = cv2.CAP_DSHOW if system == "windows" else cv2.CAP_ANY

#     cap: Optional[cv2.VideoCapture] = None
#     try:
#         cap = cv2.VideoCapture(camera_id, backend)
#         if not cap.isOpened():
#             raise RuntimeError(f"Không mở được camera tại '{camera_id}' (backend: {backend})")

#         # Set properties với validation
#         if not cap.set(cv2.CAP_PROP_FRAME_WIDTH, width):
#             print(f"Cảnh báo: Không set được width={width}")
#         if not cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height):
#             print(f"Cảnh báo: Không set được height={height}")
#         if not cap.set(cv2.CAP_PROP_FPS, fps):
#             print(f"Cảnh báo: Không set được fps={fps}")

#         actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#         actual_fps = cap.get(cv2.CAP_PROP_FPS)
#         print(f"Opened: {actual_w}x{actual_h} @ {actual_fps:.1f} fps | ID: {camera_id}")

#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 print("Frame dropped – camera disconnected?")
#                 break

#             cv2.imshow("Webcam – Nhấn q hoặc ESC để thoát", frame)
#             key = cv2.waitKey(1) & 0xFF
#             if key in (ord('q'), 27):
#                 break

#     except Exception as e:
#         raise RuntimeError(f"Runtime error khi mở webcam: {str(e)}") from e

#     finally:
#         if cap is not None:
#             cap.release()
#         cv2.destroyAllWindows()
#         print("Resources released.")


# if __name__ == "__main__":
#     try:
#         # Khuyến nghị: dùng explicit path trên Ubuntu
#         open_webcam(camera_id="/dev/video0", auto_detect=False)

#         # Nếu muốn auto-detect mà không popup lặp → dùng list_linux_cameras()
#         # open_webcam(auto_detect=True)

#     except RuntimeError as e:
#         print(f"Lỗi: {e}")
#         print("\nUbuntu-specific fixes:")
#         print("  • Đảm bảo user trong group video: groups | grep video")
#         print("  • Kiểm tra quyền: ls -l /dev/video*  (nên crw-rw----+ root video)")
#         print("  • Cài v4l-utils để detect tốt hơn: sudo apt install v4l-utils")
#         print("  • Test camera ngoài OpenCV: guvcview -d /dev/video0")


# from schemas.sub_agent import SubAgentCustomCreate
# from common.create_sub_agent import create_sub_agent
# from langchain_core.messages import HumanMessage

# sub_agent = SubAgentCustomCreate(
#     description="Bạn là chuyên gia phân tích thông tin của một tài liệu, nhiệm vụ của bạn là phân tích chi tiết tài liệu xem nó thể hiện điều gì",
#     name="Agent phân tích tài liệu",
#     project_id=1,
#     category_id=1,
#     document_name="Tài liệu về kinh doanh",
# )


# async def main():

#     agent , compiled_agent = await create_sub_agent(
#         "tai_lieu_mat",
#         sub_agent,
#         # data_context=[
#         #     """Công ty: NOVAGEN DYNAMICS Tài liệu: Internal Strategic Brief 2026 Mức độ: Confidential – 
#         # Internal Use Only 1. Tổng quan công ty  NovaGen Dynamics là công ty công nghệ chuyên phát 
#         # triển hệ thống tối ưu hoá hành vi người dùng dựa trên AI dự đoán vi mô (micro-predictive AI modeling). 
#         #   Công ty hiện có 3 dòng sản phẩm chính:  NG Insight Engine – Phân tích hành vi người dùng theo thời gian thực 
#         #     NG Persona Drift Tracker – Theo dõi sự thay đổi động cơ cá nhân  NG Influence Layer – Hệ thống điều chỉnh trải nghiệm dựa trên chỉ số cảm xúc 
#         #       NovaGen không bán dữ liệu người dùng. Thay vào đó, công ty cung cấp "behavior optimization layer" cho các nền tảng thương mại điện tử và giáo dục. 
#         #         2. Công nghệ lõi – Mô hình AURORA-7  AURORA-7 là mô hình AI nội bộ được huấn luyện theo phương pháp:  Behavioral Entropy Mapping (BEM) 
#         #           Intent Fracture Detection (IFD)  Adaptive Influence Loop (AIL)  Khác với mô hình LLM truyền thống, AURORA-7 không tập trung vào ngôn ngữ mà 
#         #           tập trung vào:  Dự đoán hành vi trước khi người dùng nhận thức được ý định  Phân tích độ dao động trong quyết định vi mô (micro-decision volatility)  
#         #           Chỉ số nội bộ:  Predictive Alignment Score (PAS): 0.82  Behavioral Drift Latency (BDL): 1.7 giờ  Influence Elasticity Index (IEI): 0.63  3. Vấn đề nội bộ 
#         #           (Chỉ dành cho Ban điều hành)  Báo cáo Q4/2025 cho thấy:  Tỷ lệ “Over-Optimization Fatigue” (OOF) tăng 18%  Một số người dùng phản ứng tiêu cực khi hệ thống tối ưu quá
#         #             chính xác  3 đối tác giáo dục yêu cầu giảm mức Influence Layer xuống 0.4  Có lo ngại rằng:  Khi Predictive Alignment vượt 0.85, người dùng bắt đầu có phản ứng phòng vệ 
#         #             tâm lý.  Ban R&D đề xuất:  Giới hạn PAS ở mức 0.83  Thêm Noise Injection 3% vào mô hình AIL  Tạo cảm giác “tự do lựa chọn” giả lập (Perceived Autonomy Buffer) 
#         #               4. Rủi ro chiến lược  Nếu dữ liệu về Influence Elasticity bị rò rỉ, công ty có thể bị điều tra về thao túng hành vi.  Đối thủ HelixMind đang phát triển mô hình
#         #                 tương tự nhưng tập trung vào dopamine-trigger modeling.  Có khả năng EU sẽ ban hành luật “Cognitive Manipulation Disclosure Act” trong 2027.  5. Kế hoạch 2026
#         #                     Mở rộng sang thị trường Đông Nam Á  Triển khai thử nghiệm “Adaptive Scarcity Signals” 
#         #   Tích hợp Emotional Volatility API vào sản phẩm thương mại . Tôi bạn muốn nhớ kỹ những 
#         #   thông tin này để nao toi hỏi bạn còn trả lời"""
#         # ],
#         status=False
#     )
#     quesion = "Báo cáo Q4/2025 cho thấy điều gì?"

#     config = {
#             "configurable": {
#                 "thread_id": sub_agent.project_id + sub_agent.category_id,
#                 "user_id": sub_agent.project_id + sub_agent.category_id
#             },
#             "recursion_limit": 10,
#         }

            
#     input_payload = {"messages": [
#         HumanMessage(content=quesion)],

#                         }
#     result = await agent.ainvoke(
#         input_payload,
#         config
#     )
#     print("Kết quả phân tích:")
#     print(result["messages"][-1].content)







# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

# import asyncio
# from kreuzberg import extract_file, ExtractionConfig

# async def main() -> None:
#     config = ExtractionConfig(
#         use_cache=True,
#         output_format="markdown",
#         enable_quality_processing=True
#     )
#     result = await extract_file("doc\DoChiHieu_履歴書.pdf", config=config)
#     print(result.content)

# asyncio.run(main())



from deepagents import create_deep_agent, CompiledSubAgent
from langchain.agents import create_agent
from common.export_models_llm import ModelsLLM
from memory.elasticsearch_saver import ElasticsearchCheckpointSaver
from config.es import init_elasticsearch_sync
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool, ToolRuntime

# Create a custom agent graph

DOCUMMET = """# CURRICULUM VITAE

## 1. Personal Information

- Full Name: Nguyễn Minh Khôi
- Date of Birth: 15/08/1994
- Phone: +84 912 345 678
- Email: khoi.nguyen.dev@gmail.com
- Location: Ho Chi Minh City, Vietnam
- LinkedIn: https://linkedin.com/in/khoinguyen-dev
- GitHub: https://github.com/khoinguyen-dev

---

## 2. Professional Summary

Senior Software Engineer with 8+ years of experience in backend systems, distributed architecture, and cloud-native applications. 
Strong background in building scalable microservices, event-driven systems, and high-performance APIs. 
Experienced in leading engineering teams, mentoring junior developers, and driving architectural decisions in enterprise environments.

Core focus areas include:
- Distributed Systems
- Microservices Architecture
- Cloud Infrastructure (AWS)
- DevOps & CI/CD Automation
- System Design & Performance Optimization

---

## 3. Technical Skills

### Programming Languages
- Java (Advanced)
- Python (Advanced)
- Go (Intermediate)
- TypeScript (Intermediate)

### Backend Frameworks
- Spring Boot
- FastAPI
- Express.js

### Frontend
- ReactJS
- Next.js
- Redux Toolkit

### Databases
- PostgreSQL
- MySQL
- MongoDB
- Redis

### Cloud & DevOps
- AWS (EC2, ECS, EKS, S3, RDS, Lambda)
- Docker
- Kubernetes
- Terraform
- GitHub Actions
- Jenkins

### Architecture & Concepts
- Microservices
- Event-Driven Architecture
- CQRS
- Domain-Driven Design
- RESTful API Design
- gRPC
- Kafka
- System Observability (Prometheus, Grafana)

---

## 4. Work Experience

### Senior Backend Engineer  
**TechNova Solutions**  
Jan 2021 – Present

Responsibilities:
- Designed and implemented microservices-based architecture serving over 2 million monthly active users.
- Led migration from monolithic architecture to containerized microservices using Kubernetes.
- Built high-throughput event processing system using Apache Kafka (handling ~50k events/sec).
- Improved API response time by 35% through database indexing and query optimization.
- Introduced CI/CD pipelines reducing deployment time from 2 hours to 15 minutes.
- Mentored 5 junior engineers and conducted system design reviews.

Key Achievements:
- Reduced infrastructure cost by 22% via resource optimization and autoscaling strategies.
- Achieved 99.95% system uptime in production.

---

### Backend Engineer  
**FinEdge Technology**  
Jun 2018 – Dec 2020

Responsibilities:
- Developed RESTful APIs for fintech payment platform.
- Integrated third-party payment gateways and banking APIs.
- Implemented JWT-based authentication and RBAC authorization.
- Built fraud detection support modules using rule-based logic.

Key Achievements:
- Successfully handled peak traffic of 10k concurrent users during major campaigns.
- Reduced transaction failure rate from 3.8% to 1.2%.

---

### Software Developer  
**GlobalSoft Vietnam**  
Jul 2016 – May 2018

Responsibilities:
- Maintained internal enterprise resource management system.
- Developed reporting modules and automated data processing pipelines.
- Supported migration from on-premise infrastructure to AWS cloud.

---

## 5. Education

Bachelor of Information Technology  
University of Science – Vietnam National University  
2012 – 2016  
GPA: 3.4 / 4.0

---

## 6. Certifications

- AWS Certified Solutions Architect – Associate (2022)
- Certified Kubernetes Administrator (CKA) (2023)

---

## 7. Leadership & Activities

- Tech Lead for internal architecture guild (2022 – Present)
- Speaker at local DevOps Meetup (Topic: Scaling Microservices with Kubernetes)
- Organized internal training sessions on Clean Architecture & DDD

---

## 8. Open Source Contributions

- Contributor to internal open-source logging framework.
- Built personal project: Distributed Task Queue using Go + Redis.
- Published several technical blogs about system design and performance optimization.

---

## 9. Languages

- Vietnamese: Native
- English: Professional Working Proficiency (IELTS 7.0)

---

## 10. References

Available upon request."""
es_sub_agent = init_elasticsearch_sync(index_elastic="sub_agent_1")
checkpoint_sub_agent = ElasticsearchCheckpointSaver(es=es_sub_agent, index="sub_agent_1", status= False)

custom_graph = create_agent(
    model=ModelsLLM.llm_ollama_gpt,
    checkpointer=checkpoint_sub_agent,
    system_prompt="Bạn là một trợ lý tra cứu, phân tích tài liệu, nhiệm vụ của bạn là phân tích tài liệu tôi đưa vào và trả lời với những gì cớ trong tài liệu có thôi."
)

config = {
    "configurable": {
        "thread_id": "abc_123",
         "user_id": "sub_agent"
    },
    "recursion_limit": 10,
}
# user_input = f"Phân tích tôi tài liệu CV của người này cho toi, đánh giá CV này: {DOCUMMET}"
user_input = "CV trên là của ai ?"
result =  custom_graph.invoke(
    {"messages": [HumanMessage(content=user_input)]}, config=config
)


print(result)

from typing import Optional, Dict, Any, Annotated
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field, ValidationError
from langchain_core.tools import InjectedToolArg

class SubAgentQueryInput(BaseModel):
    """
    Input schema for querying sub-agent memory.
    """
    question: str = Field(..., min_length=1, description="Câu hỏi đã được rewrite dựa trên lịch sử chat")
    thread_id: str = Field(..., min_length=1, description="Thread ID của sub agent")


@tool(
    description="Truy xuất và phân tích tài liệu đã được sub-agent xử lý trước đó"
)
def process_mes_history_sub_agent(question: str, runtime: Annotated[ToolRuntime, InjectedToolArg]) -> str:
    """
    Tool gọi đến custom_graph (sub-agent) để truy xuất tài liệu đã lưu trong memory.
    """

    try:
        # Validate input
        validated_input = SubAgentQueryInput(
            question=question,
            thread_id= runtime.config.get("configurable").get("thread_id")
        )

        config: Dict[str, Any] = {
            "configurable": {
                "thread_id": validated_input.thread_id,
                "user_id": "sub_agent"
            },
            "recursion_limit": 10,
        }

        response = custom_graph.invoke(
            {"messages": [HumanMessage(content=validated_input.question)]},
            config=config
        )

        if not response or "messages" not in response:
            raise RuntimeError("Sub-agent returned invalid response structure")

        # Lấy message cuối cùng của assistant
        final_message = response["messages"][-1]

        if not hasattr(final_message, "content"):
            raise RuntimeError("Sub-agent response does not contain content")

        return final_message.content

    except ValidationError as ve:
        return f"Input validation error: {ve}"

    except Exception as e:
        return f"Sub-agent execution error: {str(e)}"

# # Use it as a custom subagent
# custom_subagent = CompiledSubAgent(
#     name="data-analyzer",
#     description="Bạn là chuyên viên chuyên trách các nhiệm vụ phân tích dữ liệu phức tạp. Nhiệm vụ của bạn là khi mà người dùng hỏi về tài liệu thì bạn hãy trả lời cho họ.",
#     runnable=custom_graph
# )


research_instructions = """Bạn là supervisor agent.

QUY TẮC BẮT BUỘC:
- Nếu câu hỏi liên quan đến tài liệu hoặc CV, bạn PHẢI gọi tool `process_mes_history_sub_agent`.
"""


# subagents = [custom_subagent]


checkpoint_agent = MemorySaver()

agent = create_deep_agent(
    model= ModelsLLM.llm_ollama_gpt,
    checkpointer= checkpoint_agent,
    system_prompt=research_instructions,
    tools=[process_mes_history_sub_agent]
    # subagents=subagents
)

user_input = "Tôi muốn biết trong tài liệu tôi vừa gửi thì họ tên là gì?"
result =  agent.invoke(
    {"messages": [HumanMessage(content=user_input)]}, config=config
)


print(result)
