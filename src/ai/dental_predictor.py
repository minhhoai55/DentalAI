"""
Module dự đoán sử dụng mô hình CNN đã huấn luyện
"""

import os
import numpy as np
import tensorflow as tf
from PIL import Image
from src.models.cnn_model import DentalCNNModel

class DentalPredictor:
    """
    Lớp để dự đoán tình trạng răng miệng sử dụng mô hình CNN
    """

    def __init__(self, model_path=None):
        """
        Khởi tạo predictor

        Args:
            model_path: Đường dẫn đến file mô hình đã huấn luyện
        """
        self.model = DentalCNNModel()
        self.class_names = ['normal', 'cavity', 'gingivitis', 'plaque']
        self.class_descriptions = {
            'normal': 'Răng miệng bình thường, không có vấn đề đáng chú ý',
            'cavity': 'Phát hiện dấu hiệu sâu răng',
            'gingivitis': 'Phát hiện dấu hiệu viêm nướu',
            'plaque': 'Phát hiện cao răng hoặc mảng bám'
        }

        if model_path and os.path.exists(model_path):
            self.model.load_model(model_path)
        else:
            print("Cảnh báo: Không tìm thấy mô hình đã huấn luyện")

    def preprocess_image(self, image):
        """
        Tiền xử lý ảnh trước khi dự đoán

        Args:
            image: PIL Image hoặc numpy array

        Returns:
            numpy array: Ảnh đã được xử lý
        """
        if isinstance(image, np.ndarray):
            img_array = image
        else:
            img_array = np.array(image)

        # Resize về kích thước mong muốn
        img_array = tf.image.resize(img_array, (224, 224))

        # Normalize
        img_array = img_array / 255.0

        # Thêm batch dimension
        img_array = np.expand_dims(img_array, axis=0)

        return img_array

    def predict(self, image):
        """
        Dự đoán tình trạng răng miệng từ ảnh

        Args:
            image: PIL Image hoặc đường dẫn đến file ảnh

        Returns:
            dict: Kết quả dự đoán
        """
        try:
            # Load ảnh nếu là đường dẫn
            if isinstance(image, str):
                image = Image.open(image)

            # Preprocess
            processed_image = self.preprocess_image(image)

            # Dự đoán
            predictions, predicted_class = self.model.predict(processed_image[0])

            # Tạo kết quả
            result = {
                'success': True,
                'predicted_class': predicted_class,
                'description': self.class_descriptions.get(predicted_class, 'Không xác định'),
                'confidence': float(np.max(predictions)),
                'all_probabilities': {
                    class_name: float(prob)
                    for class_name, prob in zip(self.class_names, predictions)
                }
            }

            return result

        except Exception as e:
            return {
                'success': False,
                'error': f'Lỗi khi dự đoán: {str(e)}'
            }

    def get_regions_of_interest(self, image, prediction_result):
        """
        Xác định các vùng cần chú ý dựa trên kết quả dự đoán

        Args:
            image: PIL Image
            prediction_result: Kết quả từ predict()

        Returns:
            list: Danh sách các vùng có vấn đề
        """
        regions = []

        if not prediction_result['success']:
            return regions

        predicted_class = prediction_result['predicted_class']
        confidence = prediction_result['confidence']

        # Logic đơn giản: nếu confidence > 0.7 và không phải normal
        if confidence > 0.7 and predicted_class != 'normal':
            # Tạo một vùng giả định ở giữa ảnh (có thể cải thiện với segmentation model)
            img_width, img_height = image.size
            center_x = img_width // 2
            center_y = img_height // 2

            regions.append([
                [center_x, center_y],
                prediction_result['description']
            ])

        return regions