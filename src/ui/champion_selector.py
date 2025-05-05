from PyQt6.QtWidgets import QVBoxLayout, QLabel, QComboBox, QFrame, QHBoxLayout
from .base_ui import BaseUI
from src.logger import logger

class ChampionSelector(BaseUI):
    def __init__(self):
        super().__init__()
        self.champion_dropdown = None
        self.setup_champion_selector()

    def setup_champion_selector(self):
        """Set up the champion selector components"""
        if self.layout() is None:
            layout = QVBoxLayout()
            self.setLayout(layout)
        else:
            layout = self.layout()
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Create container frame
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1e2021;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(4)
        container_layout.setContentsMargins(8, 8, 8, 8)

        # Add dropdown label
        dropdown_label = QLabel("Select Champion:")
        dropdown_label.setStyleSheet("font-size: 14px; color: #cccccc; margin-bottom: 2px;")
        container_layout.addWidget(dropdown_label)

        # Create horizontal layout for dropdown
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(8)
        selector_layout.setContentsMargins(0, 0, 0, 0)

        # Add dropdown
        self.champion_dropdown = QComboBox()
        self.champion_dropdown.setMinimumWidth(220)
        self.champion_dropdown.setMaximumWidth(350)
        self.champion_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 4px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox:hover {
                border: 1px solid #4d4d4d;
            }
            QComboBox:on {
                border: 1px solid #ff4444;
            }
        """)
        selector_layout.addWidget(self.champion_dropdown)

        # Add selector layout to container
        container_layout.addLayout(selector_layout)

        # Add container to main layout
        layout.addWidget(container)

    def populate_champions(self, champions):
        """Populate the dropdown with champions"""
        logger.debug(f"Populating champion dropdown with {len(champions)} champions")
        self.champion_dropdown.clear()
        for champion in champions:
            self.champion_dropdown.addItem(champion)
        logger.debug("Champion dropdown populated")

    def get_selected_champion(self):
        """Get the currently selected champion"""
        champion = self.champion_dropdown.currentText()
        logger.debug(f"Current selected champion: {champion}")
        return champion
        
    def connect_selection_changed(self, callback):
        """Connect the dropdown's selection changed signal to a callback"""
        self.champion_dropdown.currentIndexChanged.connect(callback) 