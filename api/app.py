"""
Flask Web Server for Dental Analysis AI.
Cung cấp API endpoint để frontend có thể gọi và phân tích ảnh.
"""
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gemini_client import GeminiClient
try:
    from src.ai.dental_predictor import DentalPredictor
    CNN_AVAILABLE = True
except ImportError:
    CNN_AVAILABLE = False
    print("⚠️  CNN predictor not available")

# Try to import YOLO (optional)
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  YOLOv8 not installed. Install: pip install ultralytics")

# Import Computer Vision tooth detector
try:
    from tooth_detector import detect_damaged_teeth, draw_detections as cv_draw_detections
    CV_DETECTOR_AVAILABLE = True
    print("✅ CV Tooth Detector loaded")
except ImportError as e:
    CV_DETECTOR_AVAILABLE = False
    print(f"⚠️  CV tooth detector not available: {e}")

# Import Simple tooth detector (better accuracy)
try:
    from simple_tooth_detector import detect_individual_teeth, draw_simple_detections
    SIMPLE_DETECTOR_AVAILABLE = True
    print("✅ Simple Tooth Detector loaded")
except ImportError as e:
    SIMPLE_DETECTOR_AVAILABLE = False
    print(f"⚠️  Simple tooth detector not available: {e}")

def draw_yolo_annotations(image_path, detections):
    """
    Vẽ bounding boxes từ YOLO detections
    
    Args:
        image_path: Đường dẫn ảnh
        detections: List các detection từ YOLO
    
    Returns:
        Đường dẫn ảnh đã vẽ
    """
    import cv2
    
    print(f"🎨 Drawing {len(detections)} bounding boxes on {image_path}")
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Cannot read image: {image_path}")
        return image_path
    
    print(f"  Image size: {img.shape}")
    
    # Color map for 7 classes
    colors = {
        'Data caries': (0, 0, 255),           # Red
        'Mouth Ulcer': (255, 0, 255),         # Magenta
        'Tooth Discoloration': (0, 255, 255), # Yellow
        'hypodontia': (255, 165, 0),          # Orange
        'Gingivitis': (0, 165, 255),          # Orange-Red
        'Calculus': (255, 255, 0),            # Cyan
        'Caries_Gingivitus_ToothDiscoloration_Ulcer': (128, 0, 128)  # Purple
    }
    
    # Draw each detection
    for i, det in enumerate(detections):
        class_name = det.get('class_name', 'Unknown')
        confidence = det.get('confidence', 0)
        bbox = det.get('bbox', {})
        
        x1 = int(bbox.get('x1', 0))
        y1 = int(bbox.get('y1', 0))
        x2 = int(bbox.get('x2', 0))
        y2 = int(bbox.get('y2', 0))
        
        print(f"  Box {i+1}: {class_name} at ({x1},{y1})-({x2},{y2})")
        
        color = colors.get(class_name, (255, 255, 255))
        
        # Draw rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        
        # Draw label background
        label = f"{class_name} {confidence:.2%}"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(img, (x1, y1-35), (x1+w+10, y1), color, -1)
        
        # Draw label text
        cv2.putText(img, label, (x1+5, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Save annotated image
    annotated_path = image_path.replace('.', '_detected.')
    success = cv2.imwrite(annotated_path, img)
    print(f"  {'✅' if success else '❌'} Saved to: {annotated_path}")
    
    return annotated_path

def draw_annotations(image_path, problems):
    """Vẽ khoanh vùng các vấn đề trên ảnh."""
    # Đọc ảnh bằng OpenCV
    img = cv2.imread(image_path)
    overlay = img.copy()
    
    # Vẽ khoanh vùng cho mỗi vấn đề
    for loc, desc in problems:
        x, y = loc
        x, y = int(x), int(y)
        
        # Vẽ vùng highlight bán trong suốt
        cv2.circle(overlay, (x, y), 30, (0, 0, 255), -1)
        
        # Vẽ viền vòng tròn
        cv2.circle(img, (x, y), 30, (0, 0, 255), 2)
        
        # Thêm box chứa text
        (w, h), _ = cv2.getTextSize(desc, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x+10, y-25), (x+10+w, y-10), (255, 255, 255), -1)
        cv2.rectangle(img, (x+10, y-25), (x+10+w, y-10), (0, 0, 255), 1)
        
        # Thêm text mô tả
        cv2.putText(img, desc, (x+10, y-12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # Kết hợp ảnh gốc với overlay
    alpha = 0.3
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    # Lưu ảnh đã đánh dấu
    annotated_path = image_path.replace('.', '_annotated.')
    cv2.imwrite(annotated_path, img)
    return annotated_path

# Thiết lập đường dẫn tuyệt đối từ thư mục gốc của dự án
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
frontend_folder = os.path.join(project_root, 'frontend')
upload_folder = os.path.join(project_root, 'uploads')

# Khởi tạo Flask app và bật CORS
app = Flask(__name__, static_folder=frontend_folder)
CORS(app)

# Cấu hình thư mục upload và tạo nếu chưa có
os.makedirs(upload_folder, exist_ok=True)
app.config['UPLOAD_FOLDER'] = upload_folder

# Khởi tạo AI clients
gemini_client = GeminiClient()

# Khởi tạo CNN predictor (nếu có mô hình)
cnn_predictor = None
if CNN_AVAILABLE:
    model_path = os.path.join(project_root, 'models', 'dental_model_final.h5')
    if os.path.exists(model_path):
        try:
            cnn_predictor = DentalPredictor(model_path)
            print(f"✅ CNN model loaded: {model_path}")
        except Exception as e:
            print(f"⚠️  CNN model error: {e}")

# Khởi tạo YOLO detection model (nếu có)
yolo_model = None
if YOLO_AVAILABLE:
    yolo_path = os.path.join(project_root, 'models', 'dental_detection_yolo.pt')
    if os.path.exists(yolo_path):
        try:
            yolo_model = YOLO(yolo_path)
            print(f"✅ YOLO Detection model loaded: {yolo_path}")
        except Exception as e:
            print(f"⚠️  YOLO model error: {e}")
    else:
        print(f"ℹ️  YOLO model not found: {yolo_path}")

@app.route('/')
def serve_index():
    """Phục vụ file index.html từ thư mục frontend."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    """Phục vụ các file tĩnh khác (css, js, images)."""
    return send_from_directory(app.static_folder, path)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Phục vụ file ảnh từ thư mục uploads."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/analyze', methods=['POST'])
def analyze_image():
    """
    API endpoint để nhận ảnh, phân tích và trả về kết quả.
    
    Kết hợp:
    1. YOLO Detection - khoanh vùng bệnh lý
    2. CNN Classification - phân loại toàn ảnh
    3. Gemini AI - phân tích chi tiết
    """
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file ảnh nào được gửi lên'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Tên file không hợp lệ'}), 400

    if file:
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        try:
            combined_result = {
                'success': True,
                'gemini_analysis': '',
                'cnn_prediction': None,
                'yolo_detections': None,
                'cv_detections': None,
                'model': 'hybrid'
            }

            # 1. Simple Tooth Detector (Best accuracy - detects individual teeth)
            if SIMPLE_DETECTOR_AVAILABLE:
                try:
                    print("🦷 Running Simple tooth detector...")
                    simple_detections = detect_individual_teeth(image_path)
                    print(f"  Found {len(simple_detections)} teeth")
                    
                    if simple_detections:
                        combined_result['cv_detections'] = {
                            'num_detections': len(simple_detections),
                            'detections': simple_detections
                        }
                        # Draw detections
                        simple_annotated_path = draw_simple_detections(image_path, simple_detections)
                        combined_result['annotated_image'] = os.path.basename(simple_annotated_path)
                        print(f"  ✅ Simple detections saved to: {simple_annotated_path}")
                    else:
                        print("  ⚠️ Simple detector found 0 teeth")
                except Exception as e:
                    print(f"⚠️  Simple Detection error: {e}")
                    import traceback
                    traceback.print_exc()

            # 2. Fallback: Computer Vision Detection
            elif CV_DETECTOR_AVAILABLE:
                try:
                    print("🔬 Running CV tooth detector...")
                    cv_detections = detect_damaged_teeth(image_path, sensitivity='medium')
                    print(f"  Found {len(cv_detections)} damaged areas")
                    
                    if cv_detections:
                        combined_result['cv_detections'] = {
                            'num_detections': len(cv_detections),
                            'detections': cv_detections
                        }
                        # Draw CV detections
                        cv_annotated_path = cv_draw_detections(image_path, cv_detections)
                        combined_result['annotated_image'] = os.path.basename(cv_annotated_path)
                        print(f"  ✅ CV detections saved to: {cv_annotated_path}")
                    else:
                        print("  ⚠️ CV found 0 detections, will try YOLO as fallback")
                except Exception as e:
                    print(f"⚠️  CV Detection error: {e}")
                    import traceback
                    traceback.print_exc()

            # 3. YOLO Detection (AI model - last resort)
            # Use YOLO if both simple and CV failed
            use_yolo = (yolo_model and 
                       (not SIMPLE_DETECTOR_AVAILABLE and not CV_DETECTOR_AVAILABLE) or 
                        combined_result.get('cv_detections') is None or 
                        combined_result.get('cv_detections', {}).get('num_detections', 0) == 0)
            
            if use_yolo:
                try:
                    # Very low confidence to detect more smaller boxes
                    results = yolo_model(image_path, conf=0.15, verbose=False)
                    detections = []
                    
                    # 7 classes from training
                    class_names = [
                        'Data caries',
                        'Mouth Ulcer',
                        'Tooth Discoloration',
                        'hypodontia',
                        'Gingivitis',
                        'Calculus',
                        'Caries_Gingivitus_ToothDiscoloration_Ulcer'
                    ]
                    
                    print(f"🔍 YOLO found {len(results[0].boxes)} detections")
                    
                    for box in results[0].boxes:
                        print(f"  Raw box data: xyxy={box.xyxy}, xywh={box.xywh}")
                        
                        class_id = int(box.cls[0])
                        
                        # Get bbox coordinates correctly
                        xyxy = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                        
                        detection = {
                            'class_id': class_id,
                            'class_name': class_names[class_id] if class_id < len(class_names) else 'Unknown',
                            'confidence': float(box.conf[0]),
                            'bbox': {
                                'x1': x1,
                                'y1': y1,
                                'x2': x2,
                                'y2': y2
                            }
                        }
                        detections.append(detection)
                        print(f"  ✓ Detection: {detection['class_name']} ({detection['confidence']:.2%}) at ({x1},{y1})-({x2},{y2})")
                    
                    combined_result['yolo_detections'] = {
                        'num_detections': len(detections),
                        'detections': detections
                    }
                    
                    # Draw YOLO annotations
                    if detections:
                        annotated_path = draw_yolo_annotations(image_path, detections)
                        combined_result['annotated_image'] = os.path.basename(annotated_path)
                        
                except Exception as e:
                    print(f"⚠️  YOLO error: {e}")

            # 2. CNN Classification
            if cnn_predictor:
                try:
                    cnn_result = cnn_predictor.predict(image_path)
                    combined_result['cnn_prediction'] = cnn_result if cnn_result.get('success') else None
                except Exception as e:
                    print(f"⚠️  CNN error: {e}")

            # 3. Gemini AI Analysis
            try:
                gemini_result = gemini_client.analyze_dental_image(image_path)
                combined_result['gemini_analysis'] = gemini_result.get('analysis', '')
            except Exception as e:
                print(f"⚠️  Gemini error: {e}")

            return jsonify(combined_result)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True, use_reloader=False)