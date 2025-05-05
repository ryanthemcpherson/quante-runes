from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                           QFrame)

class BaseUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up the base UI components"""
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #181a1b; font-family: 'Segoe UI', Arial, sans-serif; }
            QLabel { color: #f5f6fa; font-size: 15px; }
            QComboBox {
                background-color: #23272a;
                color: #f0f0f0;
                border: 1.5px solid #444857;
                border-radius: 8px;
                padding: 10px 16px;
                min-height: 36px;
                font-size: 16px;
                margin-bottom: 8px;
            }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow { image: url(down_arrow.png); width: 14px; height: 14px; }
            QComboBox QAbstractItemView {
                background-color: #23272a;
                color: #f0f0f0;
                selection-background-color: #353b3f;
                border: 1.5px solid #444857;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #23272a;
                color: #f0f0f0;
                border: 1.5px solid #444857;
                border-radius: 8px;
                padding: 10px 24px;
                min-height: 36px;
                font-size: 16px;
                font-weight: 600;
                margin-top: 8px;
                margin-bottom: 8px;
            }
            QPushButton:hover { background-color: #353b3f; }
            QPushButton:pressed { background-color: #4d4d4d; }
            QScrollArea, QScrollArea QWidget, QScrollArea QFrame {
                background-color: #181a1b;
                border: none;
            }
            QFrame {
                background-color: #23272a;
                border-radius: 16px;
                padding: 24px 28px;
                margin-bottom: 18px;
                border: 1.5px solid #23272a;
            }
            .section-title {
                color: #ff4444;
                font-size: 22px;
                font-weight: bold;
                margin-bottom: 14px;
            }
        """)

    def create_section_frame(self, title, color, content=None):
        """Create a styled section frame with title and optional content"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #23272a;
                border-radius: 16px;
                padding: 24px 28px;
                margin-bottom: 18px;
                border: 1.5px solid #23272a;
            }}
            QLabel.title {{
                color: {color};
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        title_label.setObjectName("title")
        title_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        if content is not None:
            content_label = QLabel(content)
            content_label.setStyleSheet("color: #cccccc; font-size: 15px;")
            content_label.setWordWrap(True)
            layout.addWidget(content_label)
        return frame

    def create_scroll_area(self):
        """Create a scroll area with proper styling"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll 