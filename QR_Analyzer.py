import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QListWidget,
                             QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog,
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from pyzbar.pyzbar import decode
from PIL import Image

class ImageAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image and QR Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        # Create UI elements
        self.image_list = QListWidget()
        self.image_list.setMaximumWidth(200)
        self.image_list.itemClicked.connect(self.display_image)

        self.image_view = QGraphicsView()
        self.image_scene = QGraphicsScene()
        self.image_view.setScene(self.image_scene)
        self.image_pixmap_item = None
        self.image_path = None

        self.load_folder_button = QPushButton("Load Folder")
        self.load_folder_button.clicked.connect(self.load_images)

        self.detect_qr_button = QPushButton("Detect QR Code")
        self.detect_qr_button.clicked.connect(self.detect_qr_code)
        self.detect_qr_button.setEnabled(False)

        self.qr_label = QLabel("QR Code Data:")

        # Layout setup
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.image_list)
        h_layout.addWidget(self.image_view)

        v_layout = QVBoxLayout()
        v_layout.addWidget(self.load_folder_button)
        v_layout.addWidget(self.detect_qr_button)
        v_layout.addWidget(self.qr_label)

        main_layout = QHBoxLayout()
        main_layout.addLayout(h_layout)
        main_layout.addLayout(v_layout)

        self.setLayout(main_layout)
        self.images = []
        self.selected_area = None
        self.start_pos = None
        self.end_pos = None
        self.drawing = False
    def load_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder_path:
            self.image_list.clear()
            self.images = []
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    self.images.append(os.path.join(folder_path, filename))
                    self.image_list.addItem(filename)
    def display_image(self, item):
        self.image_path = self.images[self.image_list.row(item)]
        pixmap = QPixmap(self.image_path)
        self.image_scene.clear()
        self.image_pixmap_item = QGraphicsPixmapItem(pixmap)
        self.image_scene.addItem(self.image_pixmap_item)
        self.image_view.fitInView(self.image_scene.sceneRect(), Qt.KeepAspectRatio)
        self.detect_qr_button.setEnabled(True)
        self.qr_label.setText("QR Code Data:")
        self.selected_area = None
        self.start_pos = None
        self.end_pos = None
        self.drawing = False
    def mousePressEvent(self, event):
        if self.image_pixmap_item and self.image_pixmap_item.isUnderMouse():
            self.drawing = True
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.update_selection()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_pos = event.pos()
            self.update_selection()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            self.end_pos = event.pos()
            self.update_selection()

    def update_selection(self):
        if self.start_pos and self.end_pos:
            rect = self.image_view.mapToScene(self.start_pos).boundingRect().united(
                self.image_view.mapToScene(self.end_pos).boundingRect())
            self.selected_area = rect
            self.image_scene.clear()
            self.image_scene.addItem(self.image_pixmap_item)
            self.image_scene.addRect(rect, pen=Qt.red)
    def detect_qr_code(self):
        if self.image_path and self.selected_area:
            try:
                pil_image = Image.open(self.image_path)
                x = int(self.selected_area.x())
                y = int(self.selected_area.y())
                width = int(self.selected_area.width())
                height = int(self.selected_area.height())
                cropped_image = pil_image.crop((x, y, x + width, y + height))
                decoded_data = decode(cropped_image)
                if decoded_data:
                    qr_data = ", ".join([d.data.decode('utf-8') for d in decoded_data])
                    self.qr_label.setText(f"QR Code Data: {qr_data}")
                else:
                    self.qr_label.setText("No QR code detected in the selected area.")
            except Exception as e:
                self.qr_label.setText(f"Error: {e}")
        else:
            self.qr_label.setText("Please select an image and an area.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    analyzer = ImageAnalyzer()
    analyzer.show()
    sys.exit(app.exec_())
