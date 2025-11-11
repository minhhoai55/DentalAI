# DentalAI: Hệ Thống Chẩn Đoán Sức Khỏe Răng Miệng

## Giới thiệu

DentalAI là một hệ thống chẩn đoán sơ bộ sức khỏe răng miệng dựa trên trí tuệ nhân tạo, kết hợp nhiều công nghệ AI tiên tiến để hỗ trợ sàng lọc và tư vấn ban đầu cho người dân.

## Tính năng chính

- **YOLOv8 Object Detection**: Phát hiện và định vị các tổn thương răng miệng (sâu răng, viêm nướu, cao răng, đổi màu)
- **CNN Classification**: Phân loại tình trạng tổng thể (bình thường/sâu răng/viêm nướu/mảng bám)
- **Computer Vision Fallback**: Detector thị giác truyền thống đảm bảo luôn có kết quả
- **Gemini LLM Integration**: Sinh khuyến nghị chăm sóc bằng ngôn ngữ tự nhiên
- **Web Interface**: Giao diện thân thiện, dễ sử dụng

## Cấu trúc dự án

```
├── api/                    # Backend Flask API
│   ├── app.py             # Main application
│   ├── app_hybrid.py      # Hybrid detector app
│   ├── gemini_client.py   # Gemini AI client
│   ├── tooth_detector.py  # YOLO detector
│   └── simple_tooth_detector.py  # Simple detector
├── frontend/              # Frontend web interface
│   ├── index.html        # Main page
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── src/                  # Source code
│   ├── ai/               # AI models
│   └── models/           # Model definitions
├── models/               # Trained models
├── docs/                 # Documentation
│   └── overleaf-1/       # IEEE paper LaTeX source
├── notebooks/            # Jupyter notebooks for training
└── requirements.txt      # Python dependencies
```

## Cài đặt

### Yêu cầu hệ thống
- Python 3.10+
- pip
- Git

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Cấu hình API keys

Tạo file `.env` và thêm:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Sử dụng

### Chạy ứng dụng web

```bash
cd api
python app_hybrid.py
```

Truy cập: `http://localhost:5001`

### Training models

Sử dụng các Jupyter notebooks trong thư mục notebooks:
- `train_yolo_kaggle.ipynb`: Training YOLO model
- `train_detection.ipynb`: Training detection model
- `train_kaggle.ipynb`: Training trên Kaggle dataset

## Kiến trúc hệ thống

Hệ thống sử dụng kiến trúc 3 lớp:
1. **Presentation Layer**: Web frontend (HTML/CSS/JS)
2. **Application Layer**: Flask backend
3. **Intelligence Layer**: AI models (YOLO, CNN, CV, LLM)

### Pipeline xử lý

1. Upload ảnh → 
2. Simple Detector (fallback) → 
3. CV Detector (fallback) → 
4. YOLO Detection → 
5. CNN Classification → 
6. LLM Analysis → 
7. Kết quả + Khuyến nghị

## Hiệu suất

- YOLO inference: ~120ms
- CNN classification: ~40ms
- Computer vision detector: ~25ms
- Gemini LLM: 1.2-2.5s
- Total processing: < 3s

## Tài liệu

- **IEEE Paper**: `docs/overleaf-1/main_ieee.tex`
- **API Documentation**: Xem file `api/app.py`

## Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## Tác giả

- **Khổng Minh Hoài** - Sinh viên thực hiện
- **ThS. Nguyễn Thái Khánh** - Giảng viên hướng dẫn
- **ThS. Lê Trung Hiếu** - Giảng viên hướng dẫn

*Khoa Công Nghệ Thông Tin, Trường Đại Học Đại Nam*

## License

MIT License - xem file LICENSE để biết chi tiết

## Liên hệ

Email: hoaikhong.15052004@gmail.com

---
⭐ Nếu dự án hữu ích, hãy để lại một star!