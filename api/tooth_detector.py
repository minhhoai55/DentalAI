"""
Phát hiện răng hư bằng Computer Vision (không dùng AI model)
Dựa vào màu sắc và texture để tìm vùng bất thường
"""
import cv2
import numpy as np

def detect_damaged_teeth(image_path, sensitivity='medium'):
    """
    Phát hiện răng hư dựa trên màu sắc và contrast
    
    Args:
        image_path: Đường dẫn ảnh
        sensitivity: 'low', 'medium', 'high' - độ nhạy phát hiện
    
    Returns:
        List các vùng phát hiện: [{'bbox': (x1,y1,x2,y2), 'type': 'cavity/calculus/decay', 'severity': 0-1}]
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    
    # Convert to different color spaces
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    height, width = img.shape[:2]
    detections = []
    
    # STEP 1: Detect teeth region (using edge detection + white color)
    # Find edges
    edges = cv2.Canny(gray, 50, 150)
    
    # Find white regions (teeth are white)
    lower_teeth = np.array([0, 0, 140])  # White-ish
    upper_teeth = np.array([180, 40, 255])
    teeth_mask = cv2.inRange(hsv, lower_teeth, upper_teeth)
    
    # Combine with edges
    teeth_region = cv2.bitwise_and(teeth_mask, teeth_mask, mask=cv2.dilate(edges, None, iterations=2))
    
    # Morphological operations to find teeth area
    kernel_large = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 10))
    teeth_area = cv2.morphologyEx(teeth_region, cv2.MORPH_CLOSE, kernel_large)
    teeth_area = cv2.dilate(teeth_area, kernel_large, iterations=2)
    
    # Find the largest white region (teeth area)
    teeth_contours, _ = cv2.findContours(teeth_area, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Get bounding box of teeth area
    teeth_bbox = None
    max_teeth_area = 0
    for contour in teeth_contours:
        area = cv2.contourArea(contour)
        if area > max_teeth_area and area > (width * height * 0.05):  # At least 5% of image
            max_teeth_area = area
            x, y, w, h = cv2.boundingRect(contour)
            # Expand bbox slightly
            teeth_bbox = (
                max(0, x - 20),
                max(0, y - 20),
                min(width, x + w + 40),
                min(height, y + h + 40)
            )
    
    # If no teeth region found, use center of image
    if teeth_bbox is None:
        teeth_bbox = (
            int(width * 0.15),
            int(height * 0.30),
            int(width * 0.85),
            int(height * 0.75)
        )
    
    teeth_x1, teeth_y1, teeth_x2, teeth_y2 = teeth_bbox
    print(f"  Teeth region: ({teeth_x1},{teeth_y1})-({teeth_x2},{teeth_y2})")
    
    # 1. PHÁT HIỆN CAO RĂNG (màu vàng/nâu)
    # HSV range for yellow/brown (calculus)
    lower_yellow = np.array([15, 40, 60])
    upper_yellow = np.array([35, 255, 200])
    calculus_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # 2. PHÁT HIỆN SÂU RĂNG (màu đen/nâu đậm)
    # Detect very dark spots (cavities)
    lower_dark = np.array([0, 0, 0])
    upper_dark = np.array([180, 255, 80])
    cavity_mask = cv2.inRange(hsv, lower_dark, upper_dark)
    
    # 3. PHÁT HIỆN RĂNG ĐỔI MÀU (discoloration)
    # Detect brown/yellow stains
    lower_stain = np.array([10, 30, 40])
    upper_stain = np.array([30, 200, 180])
    stain_mask = cv2.inRange(hsv, lower_stain, upper_stain)
    
    # 4. PHÁT HIỆN VIÊM LỢI (màu đỏ)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    gum_mask = cv2.bitwise_or(red_mask1, red_mask2)
    
    # Combine masks
    combined_mask = cv2.bitwise_or(calculus_mask, cavity_mask)
    combined_mask = cv2.bitwise_or(combined_mask, stain_mask)
    
    # Morphological operations to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by size and position
    min_area = (width * height) * 0.0003  # At least 0.03% of image
    max_area = (width * height) * 0.12    # At most 12% of image
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Center of bounding box
            center_x = x + w / 2
            center_y = y + h / 2
            
            # ONLY accept detections INSIDE teeth region
            if not (teeth_x1 < center_x < teeth_x2 and teeth_y1 < center_y < teeth_y2):
                continue
            
            # Check aspect ratio (răng thường có tỉ lệ khá vuông)
            aspect_ratio = float(w) / h if h > 0 else 0
            if 0.4 < aspect_ratio < 2.5:
                
                # Determine type based on mask overlap
                roi_calculus = calculus_mask[y:y+h, x:x+w]
                roi_cavity = cavity_mask[y:y+h, x:x+w]
                roi_stain = stain_mask[y:y+h, x:x+w]
                roi_gray = gray[y:y+h, x:x+w]
                
                # Check average brightness (răng thường sáng hơn)
                avg_brightness = np.mean(roi_gray)
                if avg_brightness < 40:  # More relaxed threshold
                    continue
                
                calculus_ratio = np.sum(roi_calculus > 0) / (w * h)
                cavity_ratio = np.sum(roi_cavity > 0) / (w * h)
                stain_ratio = np.sum(roi_stain > 0) / (w * h)
                
                # Determine dominant issue
                if cavity_ratio > 0.3:
                    issue_type = 'Sâu răng'
                    severity = min(cavity_ratio * 1.5, 1.0)
                elif calculus_ratio > 0.3:
                    issue_type = 'Cao răng'
                    severity = min(calculus_ratio * 1.2, 1.0)
                elif stain_ratio > 0.2:
                    issue_type = 'Răng đổi màu'
                    severity = min(stain_ratio * 1.3, 1.0)
                else:
                    continue
                
                detection = {
                    'bbox': {
                        'x1': int(x),
                        'y1': int(y),
                        'x2': int(x + w),
                        'y2': int(y + h)
                    },
                    'class_name': issue_type,
                    'confidence': float(severity),
                    'area': float(area)
                }
                detections.append(detection)
    
    # Sort by area (largest first)
    detections.sort(key=lambda d: d['area'], reverse=True)
    
    # If no damaged teeth found, detect healthy teeth (white regions)
    if len(detections) == 0:
        print("  No damaged teeth found, detecting healthy teeth...")
        # Detect white/healthy teeth regions
        lower_white = np.array([0, 0, 150])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # Clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        
        # Find white teeth contours
        white_contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in white_contours:
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w / 2
                center_y = y + h / 2
                
                # Only in teeth region
                if (teeth_x1 < center_x < teeth_x2 and 
                    teeth_y1 < center_y < teeth_y2):
                    
                    aspect_ratio = float(w) / h if h > 0 else 0
                    if 0.4 < aspect_ratio < 2.5:
                        detection = {
                            'bbox': {
                                'x1': int(x),
                                'y1': int(y),
                                'x2': int(x + w),
                                'y2': int(y + h)
                            },
                            'class_name': 'Răng khỏe mạnh',
                            'confidence': 0.85,
                            'area': float(area)
                        }
                        detections.append(detection)
        
        detections.sort(key=lambda d: d['area'], reverse=True)
    
    # Limit to top 5 detections
    return detections[:5]


def draw_detections(image_path, detections):
    """
    Vẽ bounding boxes lên ảnh
    """
    img = cv2.imread(image_path)
    if img is None:
        return image_path
    
    colors = {
        'Sâu răng': (0, 0, 255),      # Red
        'Cao răng': (0, 255, 255),     # Yellow
        'Răng đổi màu': (255, 165, 0), # Orange
        'Viêm lợi': (255, 0, 255),     # Magenta
        'Răng khỏe mạnh': (0, 255, 0)  # Green
    }
    
    for det in detections:
        bbox = det['bbox']
        x1, y1 = bbox['x1'], bbox['y1']
        x2, y2 = bbox['x2'], bbox['y2']
        
        class_name = det['class_name']
        confidence = det['confidence']
        
        color = colors.get(class_name, (255, 0, 0))
        
        # Draw rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 4)
        
        # Draw label
        label = f"{class_name} {confidence:.0%}"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(img, (x1, y1-30), (x1+w+10, y1), color, -1)
        cv2.putText(img, label, (x1+5, y1-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Save
    output_path = image_path.replace('.', '_cv_detected.')
    cv2.imwrite(output_path, img)
    return output_path
