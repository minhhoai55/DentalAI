"""
Script tạo annotations cho object detection
Sử dụng để annotate bounding boxes cho răng sâu
"""

import cv2
import os
import json
from pathlib import Path

class DentalAnnotator:
    """
    Class để annotate dữ liệu cho object detection
    """

    def __init__(self, image_dir, label_dir):
        self.image_dir = Path(image_dir)
        self.label_dir = Path(label_dir)
        self.label_dir.mkdir(exist_ok=True)

        # Danh sách class
        self.classes = ['cavity']  # Có thể thêm gingivitis, plaque, etc.

        # Biến lưu trữ annotations
        self.current_image = None
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.rectangles = []

    def click_and_crop(self, event, x, y, flags, param):
        """Mouse callback để vẽ bounding box"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                img_copy = self.current_image.copy()
                cv2.rectangle(img_copy, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
                cv2.imshow('image', img_copy)

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            cv2.rectangle(self.current_image, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
            cv2.imshow('image', self.current_image)

            # Lưu rectangle
            rect = {
                'x1': min(self.ix, x),
                'y1': min(self.iy, y),
                'x2': max(self.ix, x),
                'y2': max(self.iy, y)
            }
            self.rectangles.append(rect)
            print(f"Đã thêm bounding box: {rect}")

    def annotate_image(self, image_path):
        """Annotate một ảnh"""
        self.current_image = cv2.imread(str(image_path))
        if self.current_image is None:
            print(f"Không thể đọc ảnh: {image_path}")
            return

        self.rectangles = []
        cv2.namedWindow('image')
        cv2.setMouseCallback('image', self.click_and_crop)

        print(f"Đang annotate: {image_path.name}")
        print("Hướng dẫn:")
        print("- Click và kéo để vẽ bounding box quanh răng sâu")
        print("- Nhấn 's' để lưu và tiếp tục")
        print("- Nhấn 'c' để bỏ qua ảnh này")
        print("- Nhấn 'q' để thoát")

        while True:
            cv2.imshow('image', self.current_image)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'):  # Save
                self.save_annotations(image_path)
                break
            elif key == ord('c'):  # Skip
                break
            elif key == ord('q'):  # Quit
                cv2.destroyAllWindows()
                return False

        cv2.destroyAllWindows()
        return True

    def save_annotations(self, image_path):
        """Lưu annotations theo format YOLO"""
        img_height, img_width = self.current_image.shape[:2]

        # Tạo file label
        label_file = self.label_dir / f"{image_path.stem}.txt"

        with open(label_file, 'w') as f:
            for rect in self.rectangles:
                # Convert to YOLO format (normalized)
                x_center = (rect['x1'] + rect['x2']) / 2 / img_width
                y_center = (rect['y1'] + rect['y2']) / 2 / img_height
                width = (rect['x2'] - rect['x1']) / img_width
                height = (rect['y2'] - rect['y1']) / img_height

                # Class 0 = cavity
                class_id = 0

                f.write(".6f")

        print(f"Đã lưu annotations: {label_file}")

    def annotate_directory(self, image_directory):
        """Annotate tất cả ảnh trong thư mục"""
        image_paths = list(Path(image_directory).glob("*.jpg")) + \
                     list(Path(image_directory).glob("*.png")) + \
                     list(Path(image_directory).glob("*.jpeg"))

        print(f"Tìm thấy {len(image_paths)} ảnh để annotate")

        for i, img_path in enumerate(image_paths):
            print(f"\nẢnh {i+1}/{len(image_paths)}: {img_path.name}")

            if not self.annotate_image(img_path):
                print("Dừng annotate")
                break

        print("Hoàn thành annotate!")

def main():
    """Hàm chính"""
    # Cấu hình đường dẫn
    image_dir = "data/train/cavity"  # Thư mục chứa ảnh răng sâu
    label_dir = "data/labels/train"  # Thư mục lưu annotations

    # Tạo annotator
    annotator = DentalAnnotator(image_dir, label_dir)

    # Bắt đầu annotate
    annotator.annotate_directory(image_dir)

if __name__ == "__main__":
    main()