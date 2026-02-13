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


from schemas.sub_agent import SubAgentCustomCreate
from common.create_sub_agent import create_sub_agent
from langchain_core.messages import HumanMessage

sub_agent = SubAgentCustomCreate(
    description="Bạn là chuyên gia phân tích thông tin của một tài liệu, nhiệm vụ của bạn là phân tích chi tiết tài liệu xem nó thể hiện điều gì",
    name="Agent phân tích tài liệu",
    project_id=1,
    category_id=1,
    document_name="Tài liệu về kinh doanh",
)


async def main():

    agent , compiled_agent = await create_sub_agent(
        "tai_lieu_mat",
        sub_agent,
        # data_context=[
        #     """Công ty: NOVAGEN DYNAMICS Tài liệu: Internal Strategic Brief 2026 Mức độ: Confidential – 
        # Internal Use Only 1. Tổng quan công ty  NovaGen Dynamics là công ty công nghệ chuyên phát 
        # triển hệ thống tối ưu hoá hành vi người dùng dựa trên AI dự đoán vi mô (micro-predictive AI modeling). 
        #   Công ty hiện có 3 dòng sản phẩm chính:  NG Insight Engine – Phân tích hành vi người dùng theo thời gian thực 
        #     NG Persona Drift Tracker – Theo dõi sự thay đổi động cơ cá nhân  NG Influence Layer – Hệ thống điều chỉnh trải nghiệm dựa trên chỉ số cảm xúc 
        #       NovaGen không bán dữ liệu người dùng. Thay vào đó, công ty cung cấp "behavior optimization layer" cho các nền tảng thương mại điện tử và giáo dục. 
        #         2. Công nghệ lõi – Mô hình AURORA-7  AURORA-7 là mô hình AI nội bộ được huấn luyện theo phương pháp:  Behavioral Entropy Mapping (BEM) 
        #           Intent Fracture Detection (IFD)  Adaptive Influence Loop (AIL)  Khác với mô hình LLM truyền thống, AURORA-7 không tập trung vào ngôn ngữ mà 
        #           tập trung vào:  Dự đoán hành vi trước khi người dùng nhận thức được ý định  Phân tích độ dao động trong quyết định vi mô (micro-decision volatility)  
        #           Chỉ số nội bộ:  Predictive Alignment Score (PAS): 0.82  Behavioral Drift Latency (BDL): 1.7 giờ  Influence Elasticity Index (IEI): 0.63  3. Vấn đề nội bộ 
        #           (Chỉ dành cho Ban điều hành)  Báo cáo Q4/2025 cho thấy:  Tỷ lệ “Over-Optimization Fatigue” (OOF) tăng 18%  Một số người dùng phản ứng tiêu cực khi hệ thống tối ưu quá
        #             chính xác  3 đối tác giáo dục yêu cầu giảm mức Influence Layer xuống 0.4  Có lo ngại rằng:  Khi Predictive Alignment vượt 0.85, người dùng bắt đầu có phản ứng phòng vệ 
        #             tâm lý.  Ban R&D đề xuất:  Giới hạn PAS ở mức 0.83  Thêm Noise Injection 3% vào mô hình AIL  Tạo cảm giác “tự do lựa chọn” giả lập (Perceived Autonomy Buffer) 
        #               4. Rủi ro chiến lược  Nếu dữ liệu về Influence Elasticity bị rò rỉ, công ty có thể bị điều tra về thao túng hành vi.  Đối thủ HelixMind đang phát triển mô hình
        #                 tương tự nhưng tập trung vào dopamine-trigger modeling.  Có khả năng EU sẽ ban hành luật “Cognitive Manipulation Disclosure Act” trong 2027.  5. Kế hoạch 2026
        #                     Mở rộng sang thị trường Đông Nam Á  Triển khai thử nghiệm “Adaptive Scarcity Signals” 
        #   Tích hợp Emotional Volatility API vào sản phẩm thương mại . Tôi bạn muốn nhớ kỹ những 
        #   thông tin này để nao toi hỏi bạn còn trả lời"""
        # ],
        status=False
    )
    quesion = "Báo cáo Q4/2025 cho thấy điều gì?"

    config = {
            "configurable": {
                "thread_id": sub_agent.project_id + sub_agent.category_id,
                "user_id": sub_agent.project_id + sub_agent.category_id
            },
            "recursion_limit": 10,
        }

            
    input_payload = {"messages": [
        HumanMessage(content=quesion)],

                        }
    result = await agent.ainvoke(
        input_payload,
        config
    )
    print("Kết quả phân tích:")
    print(result["messages"][-1].content)







if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
