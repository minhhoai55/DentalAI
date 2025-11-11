"""
Gemini API Client.
Xử lý tất cả tương tác với Gemini AI
"""
import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Tải các biến môi trường từ tệp .env
load_dotenv()

class GeminiClient:
    """Client để tương tác với Gemini API"""

    def __init__(self, api_key=None, model_name='gemini-2.5-flash'):
        """
        Khởi tạo Gemini client.
        
        Args:
            api_key (str, optional): API key. Nếu là None, sẽ lấy từ biến môi trường.
            model_name (str): Tên model để sử dụng.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("Không tìm thấy GEMINI_API_KEY trong tệp .env hoặc biến môi trường!")
        
        # Cấu hình API key cho thư viện
        genai.configure(api_key=self.api_key)
        
        # Khởi tạo model
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)

    def analyze_dental_image(self, image_path):
        """
        Phân tích ảnh răng miệng bằng cách gửi ảnh và prompt đến Gemini.
        
        Args:
            image_path (str or PIL.Image): Đường dẫn đến tệp ảnh hoặc đối tượng ảnh PIL.
            
        Returns:
            dict: Một dictionary chứa kết quả phân tích hoặc thông báo lỗi.
        """
        try:
            img = Image.open(image_path) if isinstance(image_path, str) else image_path
            
            # Đảm bảo ảnh ở chế độ RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            prompt = self._create_analysis_prompt()
            
            # Gửi yêu cầu đến Gemini và kiểm tra kết quả
            response = self.model.generate_content([prompt, img])
            
            if not response.text:
                raise Exception("Không nhận được phản hồi từ AI")
                
            # Parse regions từ phản hồi
            regions_match = re.search(r'\*\*Regions:\*\*\s*\[([\s\S]*?)\]', response.text)
            regions = []
            if regions_match:
                try:
                    regions_text = '[' + regions_match.group(1) + ']'
                    regions = json.loads(regions_text)
                except:
                    print("Failed to parse regions")

            # Kiểm tra xem phản hồi có đúng định dạng không
            if not any(marker in response.text for marker in ["**Tổng quan:**", "**Regions:**"]):
                raise Exception("Phản hồi từ AI không đúng định dạng yêu cầu")
            
            return {
                'success': True,
                'analysis': response.text,
                'regions': regions,
                'model': self.model_name
            }
        except Exception as e:
            error_message = str(e)
            if "API key not valid" in error_message:
                error_message = f"API Key không hợp lệ hoặc không có quyền truy cập model '{self.model_name}'."
            elif "Không nhận được phản hồi từ AI" in error_message:
                error_message = "AI không thể phân tích ảnh này. Vui lòng thử lại với ảnh khác hoặc chụp lại rõ hơn."
            elif "Phản hồi từ AI không đúng định dạng" in error_message:
                error_message = "Có lỗi trong quá trình phân tích. Vui lòng thử lại."
            elif "could not convert string to float" in error_message:
                error_message = "Lỗi xử lý dữ liệu. Vui lòng thử lại."
            return {
                'success': False,
                'error': error_message
            }

    def _create_analysis_prompt(self):
        """Tạo prompt yêu cầu AI phân tích ngắn gọn và có cấu trúc."""
        return """
Bạn là một chuyên gia nha khoa AI. Hãy phân tích ảnh răng và trả lời theo CHÍNH XÁC định dạng sau:

**Độ tin cậy:** {0-100}

**Tổng quan:**
- Tóm tắt tình trạng răng miệng tổng thể trong 2-3 câu. Nêu bật những vấn đề chính cần chú ý.

**Regions:**
[
  [[x1, y1], "Sâu răng số 6 hàm dưới"],
  [[x2, y2], "Viêm nướu vùng răng cửa"],
  ...
]

Trong đó:
- x, y: tọa độ pixel trên ảnh (x: 0-width, y: 0-height)
- Mô tả: ngắn gọn về vấn đề tại vị trí đó

**Phát hiện:**
- **Sâu răng:** (Mô tả vị trí và mức độ nếu có. Ghi "Không phát hiện" nếu không thấy)
- **Nướu:** (Mô tả chi tiết tình trạng viêm, sưng, màu sắc. Ghi "Bình thường" nếu không có vấn đề)
- **Cao răng/Mảng bám:** (Mô tả vị trí và mức độ. Ghi "Không phát hiện" hoặc "Ít" nếu không đáng kể)
- **Màu răng:** (Đánh giá màu sắc theo thang VITA: A1, B2, C3,...)
- **Khớp cắn:** (Nhận xét về tình trạng khớp cắn, răng lệch, chen chúc)
- **Mô mềm:** (Tình trạng lưỡi và niêm mạc miệng nếu thấy trong ảnh)

Mỗi mục phát hiện cần mô tả chi tiết trong 2-3 câu, nêu rõ:
- Vị trí cụ thể (số răng nếu có)
- Mức độ nghiêm trọng
- Đặc điểm quan sát được

**Khuyến nghị:**
- Các điều trị cần thiết (nếu có)
- Cách chăm sóc tại nhà
- Thói quen cần điều chỉnh
- Thời gian nên tái khám

**Lưu ý:** Chuẩn đoán chỉ mang tính tham khảo, cần được xác nhận bởi nha sĩ.
"""