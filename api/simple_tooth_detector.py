"""
Simple tooth detector - Detect individual teeth using edge detection and contours
Simpler approach than color-based detection
"""
import cv2
import numpy as np

def detect_individual_teeth(image_path):
    """
    Phát hiện từng răng riêng lẻ bằng edge detection
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply bilateral filter to reduce noise while keeping edges sharp
    bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Apply adaptive thresholding to get teeth regions
    adaptive = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
    
    # Invert (teeth should be white)
    adaptive_inv = cv2.bitwise_not(adaptive)
    
    # Find contours
    contours, _ = cv2.findContours(adaptive_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detections = []
    min_area = (width * height) * 0.0005  # 0.05% of image
    max_area = (width * height) * 0.03    # 3% of image
    
    # Center region where teeth should be
    center_x_min = width * 0.25
    center_x_max = width * 0.75
    center_y_min = height * 0.35
    center_y_max = height * 0.65
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Center of detection
            cx = x + w/2
            cy = y + h/2
            
            # Only in center region
            if not (center_x_min < cx < center_x_max and center_y_min < cy < center_y_max):
                continue
            
            # Aspect ratio check (teeth are roughly rectangular)
            aspect = w / h if h > 0 else 0
            if not (0.5 < aspect < 2.0):
                continue
            
            # Check if region is bright enough (teeth are white)
            roi = gray[y:y+h, x:x+w]
            avg_brightness = np.mean(roi)
            
            if avg_brightness > 100:  # Bright enough to be a tooth
                # Check for yellow/brown stains
                roi_color = img[y:y+h, x:x+w]
                hsv_roi = cv2.cvtColor(roi_color, cv2.COLOR_BGR2HSV)
                
                # Yellow/brown range
                lower_stain = np.array([10, 30, 30])
                upper_stain = np.array([30, 255, 200])
                stain_mask = cv2.inRange(hsv_roi, lower_stain, upper_stain)
                stain_ratio = np.sum(stain_mask > 0) / (w * h)
                
                # Classify
                if stain_ratio > 0.15:
                    class_name = 'Cao răng'
                    confidence = min(stain_ratio * 2, 0.95)
                else:
                    class_name = 'Răng khỏe mạnh'
                    confidence = 0.85
                
                detection = {
                    'bbox': {
                        'x1': int(x),
                        'y1': int(y),
                        'x2': int(x + w),
                        'y2': int(y + h)
                    },
                    'class_name': class_name,
                    'confidence': float(confidence),
                    'area': float(area)
                }
                detections.append(detection)
    
    # Sort by x position (left to right)
    detections.sort(key=lambda d: d['bbox']['x1'])
    
    # Limit to 8 teeth (visible teeth in image)
    return detections[:8]


def draw_simple_detections(image_path, detections):
    """
    Vẽ bounding boxes đơn giản
    """
    img = cv2.imread(image_path)
    if img is None:
        return image_path
    
    for det in detections:
        bbox = det['bbox']
        x1, y1 = bbox['x1'], bbox['y1']
        x2, y2 = bbox['x2'], bbox['y2']
        
        class_name = det['class_name']
        confidence = det['confidence']
        
        # Color based on class
        if class_name == 'Răng khỏe mạnh':
            color = (0, 255, 0)  # Green
        else:
            color = (0, 255, 255)  # Yellow for calculus
        
        # Draw rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        
        # Draw label
        label = f"{class_name} {confidence:.0%}"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img, (x1, y1-25), (x1+w+10, y1), color, -1)
        cv2.putText(img, label, (x1+5, y1-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    # Save
    output_path = image_path.replace('.', '_simple_detected.')
    cv2.imwrite(output_path, img)
    return output_path
