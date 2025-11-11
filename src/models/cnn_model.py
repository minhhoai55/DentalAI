"""
Định nghĩa mô hình CNN cho phân tích răng miệng
File này chứa kiến trúc mô hình và các hàm liên quan
"""

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import os

class DentalCNNModel:
    """
    Lớp mô hình CNN cho phân tích răng miệng
    """

    def __init__(self, input_shape=(224, 224, 3), num_classes=4):
        """
        Khởi tạo mô hình

        Args:
            input_shape: Kích thước đầu vào (height, width, channels)
            num_classes: Số lớp phân loại
        """
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = None

    def create_model(self):
        """
        Tạo kiến trúc mô hình CNN
        """
        model = Sequential([
            # Block 1
            Conv2D(32, (3, 3), activation='relu', input_shape=self.input_shape, padding='same'),
            BatchNormalization(),
            Conv2D(32, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            MaxPooling2D(2, 2),
            Dropout(0.25),

            # Block 2
            Conv2D(64, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            Conv2D(64, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            MaxPooling2D(2, 2),
            Dropout(0.25),

            # Block 3
            Conv2D(128, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            Conv2D(128, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            MaxPooling2D(2, 2),
            Dropout(0.25),

            # Block 4
            Conv2D(256, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            Conv2D(256, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            MaxPooling2D(2, 2),
            Dropout(0.25),

            # Fully Connected layers
            Flatten(),
            Dense(512, activation='relu'),
            BatchNormalization(),
            Dropout(0.5),
            Dense(256, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            Dense(self.num_classes, activation='softmax')
        ])

        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )

        self.model = model
        return model

    def load_weights(self, weights_path):
        """
        Load trọng số đã huấn luyện

        Args:
            weights_path: Đường dẫn đến file trọng số
        """
        if self.model is None:
            self.create_model()
        self.model.load_weights(weights_path)
        print(f"Đã load trọng số từ: {weights_path}")

    def load_model(self, model_path):
        """
        Load toàn bộ mô hình đã lưu

        Args:
            model_path: Đường dẫn đến file mô hình
        """
        self.model = tf.keras.models.load_model(model_path)
        print(f"Đã load mô hình từ: {model_path}")

    def predict(self, image):
        """
        Dự đoán trên một ảnh

        Args:
            image: Ảnh đầu vào (numpy array hoặc PIL Image)

        Returns:
            tuple: (predictions, class_names)
        """
        if self.model is None:
            raise ValueError("Mô hình chưa được tạo hoặc load")

        # Preprocess image
        if isinstance(image, np.ndarray):
            img_array = image
        else:
            # Assume PIL Image
            img_array = np.array(image)

        # Resize và normalize
        img_array = tf.image.resize(img_array, (self.input_shape[0], self.input_shape[1]))
        img_array = img_array / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Predict
        predictions = self.model.predict(img_array)
        predicted_class = np.argmax(predictions[0])

        # Class names (có thể customize theo dataset)
        class_names = ['normal', 'cavity', 'gingivitis', 'plaque']

        return predictions[0], class_names[predicted_class]

    def get_model_summary(self):
        """
        In tóm tắt mô hình
        """
        if self.model is None:
            print("Mô hình chưa được tạo")
            return
        self.model.summary()

def create_data_generators(data_dir, img_height=224, img_width=224, batch_size=32):
    """
    Tạo data generators cho training và validation

    Args:
        data_dir: Thư mục chứa dữ liệu
        img_height: Chiều cao ảnh
        img_width: Chiều rộng ảnh
        batch_size: Kích thước batch

    Returns:
        tuple: (train_generator, val_generator)
    """
    # Data augmentation cho training
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=0.2  # 20% cho validation
    )

    # Chỉ rescale cho validation
    val_datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

    # Training generator
    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=(img_height, img_width),
        batch_size=batch_size,
        class_mode='categorical',
        subset='training'
    )

    # Validation generator
    val_generator = val_datagen.flow_from_directory(
        data_dir,
        target_size=(img_height, img_width),
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation'
    )

    return train_generator, val_generator