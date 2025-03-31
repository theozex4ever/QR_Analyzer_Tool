import sys
import os
import cv2
import numpy as np
from datetime import datetime
from pylibdmtx import pylibdmtx
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QListWidget,
                            QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog,
                            QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                            QTabWidget, QProgressBar, QSpinBox, QTextEdit, 
                            QScrollArea, QFrame)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class MatrixProcessorThread(QThread):
    progress = pyqtSignal(int)
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, images, output_dir, scale_factor):
        super().__init__()
        self.images = images
        self.output_dir = output_dir
        self.scale_factor = scale_factor / 100.0

    def preprocess_image(self, image):
        """Preprocess image for better Data Matrix detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        denoised = cv2.fastNlMeansDenoising(thresh)
        return denoised

    def run(self):
        total_images = len(self.images)
        for i, image_path in enumerate(self.images):
            try:
                # Load and scale image
                img = cv2.imread(image_path)
                if img is None:
                    self.log_message.emit(f"Error loading image: {image_path}")
                    continue

                # Scale image if needed
                if self.scale_factor != 1.0:
                    new_width = int(img.shape[1] * self.scale_factor)
                    new_height = int(img.shape[0] * self.scale_factor)
                    img = cv2.resize(img, (new_width, new_height), 
                                    interpolation=cv2.INTER_AREA)

                # Create output directory for this image
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                image_output_dir = os.path.join(self.output_dir, base_name)
                os.makedirs(image_output_dir, exist_ok=True)

                # Process image
                processed = self.preprocess_image(img)
                decoded = pylibdmtx.decode(processed)

                if decoded:
                    # Process each detected matrix
                    for j, matrix in enumerate(decoded):
                        try:
                            # Get matrix data and location
                            data = matrix.data.decode('utf-8')
                            rect = matrix.rect
                            
                            # Add padding around the matrix
                            pad = 10
                            x = max(0, rect.left - pad)
                            y = max(0, rect.top - pad)
                            w = min(img.shape[1] - x, rect.width + 2*pad)
                            h = min(img.shape[0] - y, rect.height + 2*pad)
                            
                            # Extract and save matrix image
                            matrix_img = img[y:y+h, x:x+w]
                            safe_name = "".join(c if c.isalnum() else '_' for c in data)
                            timestamp = datetime.now().strftime("%H%M%S")
                            out_path = os.path.join(image_output_dir, 
                                                  f"{safe_name}_{timestamp}.png")
                            cv2.imwrite(out_path, matrix_img)
                            
                            self.log_message.emit(
                                f"Saved matrix from {base_name}: {data}")
                        except Exception as e:
                            self.log_message.emit(
                                f"Error processing matrix in {base_name}: {str(e)}")
                else:
                    self.log_message.emit(f"No matrices found in {base_name}")

            except Exception as e:
                self.log_message.emit(f"Error processing {base_name}: {str(e)}")

            self.progress.emit(int((i + 1) / total_images * 100))

        self.finished.emit()

class ManualAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Create UI elements
        self.image_list = QListWidget()
        self.image_list.setMaximumWidth(200)
        self.image_list.itemClicked.connect(self.display_image)

        self.image_view = QGraphicsView()
        self.image_scene = QGraphicsScene()
        self.image_view.setScene(self.image_scene)
        self.image_pixmap_item = None
        self.image_path = None
        self.current_pixmap = None
        self.cv_image = None

        self.load_folder_button = QPushButton("Load Folder")
        self.load_folder_button.clicked.connect(self.load_images)

        self.detect_matrix_button = QPushButton("Detect Data Matrix")
        self.detect_matrix_button.clicked.connect(self.detect_matrix)
        self.detect_matrix_button.setEnabled(False)

        self.matrix_label = QLabel("Data Matrix Content:")

        # Layout setup
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.image_list)
        h_layout.addWidget(self.image_view)

        v_layout = QVBoxLayout()
        v_layout.addWidget(self.load_folder_button)
        v_layout.addWidget(self.detect_matrix_button)
        v_layout.addWidget(self.matrix_label)

        main_layout = QHBoxLayout()
        main_layout.addLayout(h_layout)
        main_layout.addLayout(v_layout)

        self.setLayout(main_layout)
        self.images = []
        self.selected_area = None
        self.start_pos = None
        self.end_pos = None
        self.drawing = False

    def cv2_to_qpixmap(self, cv_img):
        """Convert OpenCV image to QPixmap"""
        height, width = cv_img.shape[:2]
        bytes_per_line = 3 * width
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        q_img = QImage(rgb_image.data, width, height, bytes_per_line, 
                    QImage.Format_RGB888)
        return QPixmap.fromImage(q_img)

    def load_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder_path:
            self.image_list.clear()
            self.images = []
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    self.images.append(os.path.join(folder_path, filename))
                    self.image_list.addItem(filename)

    def display_image(self, item):
        self.image_path = self.images[self.image_list.row(item)]
        self.cv_image = cv2.imread(self.image_path)
        if self.cv_image is not None:
            self.current_pixmap = self.cv2_to_qpixmap(self.cv_image)
            self.image_scene.clear()
            self.image_pixmap_item = QGraphicsPixmapItem(self.current_pixmap)
            self.image_scene.addItem(self.image_pixmap_item)
            self.image_view.fitInView(self.image_scene.sceneRect(), 
                                    Qt.KeepAspectRatio)
            self.detect_matrix_button.setEnabled(True)
            self.matrix_label.setText("Data Matrix Content:")
            self.selected_area = None
            self.start_pos = None
            self.end_pos = None
            self.drawing = False

    def mousePressEvent(self, event):
        pos = self.image_view.mapToScene(event.pos())
        if self.image_pixmap_item and self.image_pixmap_item.contains(pos):
            self.drawing = True
            self.start_pos = pos
            self.end_pos = pos
            self.update_selection()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_pos = self.image_view.mapToScene(event.pos())
            self.update_selection()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            self.end_pos = self.image_view.mapToScene(event.pos())
            self.update_selection()

    def update_selection(self):
        if self.start_pos and self.end_pos and self.current_pixmap:
            self.image_scene.clear()
            self.image_pixmap_item = QGraphicsPixmapItem(self.current_pixmap)
            self.image_scene.addItem(self.image_pixmap_item)
            
            x = min(self.start_pos.x(), self.end_pos.x())
            y = min(self.start_pos.y(), self.end_pos.y())
            width = abs(self.end_pos.x() - self.start_pos.x())
            height = abs(self.end_pos.y() - self.start_pos.y())
            
            self.selected_area = self.image_scene.addRect(x, y, width, height, 
                                                        pen=Qt.red)

    def preprocess_image(self, image):
        """Preprocess image for better Data Matrix detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        denoised = cv2.fastNlMeansDenoising(thresh)
        return denoised

    def detect_matrix(self):
        if self.cv_image is not None and self.selected_area:
            try:
                rect = self.selected_area.rect()
                x = max(0, int(rect.x()))
                y = max(0, int(rect.y()))
                width = min(self.cv_image.shape[1] - x, int(rect.width()))
                height = min(self.cv_image.shape[0] - y, int(rect.height()))
                
                cropped_image = self.cv_image[y:y+height, x:x+width]
                processed_image = self.preprocess_image(cropped_image)
                decoded_data = pylibdmtx.decode(processed_image)
                
                if decoded_data:
                    matrix_data = ", ".join([d.data.decode('utf-8') 
                                            for d in decoded_data])
                    self.matrix_label.setText(f"Data Matrix Content: {matrix_data}")
                else:
                    self.matrix_label.setText(
                        "No Data Matrix detected in the selected area.")
            except Exception as e:
                self.matrix_label.setText(f"Error: {e}")
        else:
            self.matrix_label.setText("Please select an image and an area.")

class AutomatedAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.processor = None

    def setup_ui(self):
        # Create UI elements
        self.image_list = QListWidget()
        self.image_list.setMaximumWidth(200)
        
        # Buttons
        self.load_folder_button = QPushButton("Load Folder")
        self.load_folder_button.clicked.connect(self.load_images)
        
        self.output_dir_button = QPushButton("Select Output Directory")
        self.output_dir_button.clicked.connect(self.select_output_dir)
        
        self.process_button = QPushButton("Process Images")
        self.process_button.clicked.connect(self.process_images)
        self.process_button.setEnabled(False)
        
        # Scaling control
        scale_layout = QHBoxLayout()
        self.scale_label = QLabel("Scale Factor (%):")
        self.scale_spinbox = QSpinBox()
        self.scale_spinbox.setRange(25, 100)
        self.scale_spinbox.setValue(100)
        self.scale_spinbox.setSingleStep(5)
        scale_layout.addWidget(self.scale_label)
        scale_layout.addWidget(self.scale_spinbox)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        
        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        
        # Layout setup
        controls_layout = QVBoxLayout()
        controls_layout.addWidget(self.load_folder_button)
        controls_layout.addWidget(self.output_dir_button)
        controls_layout.addLayout(scale_layout)
        controls_layout.addWidget(self.process_button)
        controls_layout.addWidget(self.progress_bar)
        controls_layout.addWidget(self.log_viewer)
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.image_list)
        main_layout.addLayout(controls_layout)
        
        self.setLayout(main_layout)
        self.images = []
        self.output_dir = None

    def load_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder_path:
            self.image_list.clear()
            self.images = []
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    self.images.append(os.path.join(folder_path, filename))
                    self.image_list.addItem(filename)
            self.update_process_button()

    def select_output_dir(self):
        self.output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory")
        self.update_process_button()

    def update_process_button(self):
        self.process_button.setEnabled(
            bool(self.images) and bool(self.output_dir))

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def append_log(self, message):
        self.log_viewer.append(message)

    def process_complete(self):
        self.progress_bar.setValue(100)
        self.append_log("Processing complete!")
        self.process_button.setEnabled(True)
        self.processor = None

    def process_images(self):
        if not self.images or not self.output_dir:
            return

        self.process_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_viewer.clear()
        self.append_log("Starting image processing...")

        self.processor = MatrixProcessorThread(
            self.images, self.output_dir, self.scale_spinbox.value())
        self.processor.progress.connect(self.update_progress)
        self.processor.log_message.connect(self.append_log)
        self.processor.finished.connect(self.process_complete)
        self.processor.start()

class ImageAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image and Data Matrix Analyzer")
        self.setGeometry(100, 100, 1200, 800)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.manual_analyzer = ManualAnalyzer()
        self.automated_analyzer = AutomatedAnalyzer()
        
        self.tab_widget.addTab(self.manual_analyzer, "Manual Analysis")
        self.tab_widget.addTab(self.automated_analyzer, "Automated Processing")

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    analyzer = ImageAnalyzer()
    analyzer.show()
    sys.exit(app.exec_())
