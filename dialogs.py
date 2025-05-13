from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class CleaningDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cleaning Progress")
        self.setFixedSize(200, 105)
        self.setModal(True)
        self.setStyleSheet("background-color: #0E5053;")
        
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Cleaning...")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: white;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-weight: bold; color: white;")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setVisible(False)
        layout.addWidget(self.result_label)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setVisible(False)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        
        layout.addStretch()

class RestartDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Restart Required")
        self.setFixedSize(300, 120)
        self.setModal(True)
        self.setStyleSheet("background-color: #0E5053;")
        
        layout = QVBoxLayout(self)
        
        self.message_label = QLabel("Mouse settings optimized. A system restart is required for changes to take effect.")
        self.message_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        button_layout = QHBoxLayout()
        
        self.restart_now_button = QPushButton("Restart Now")
        self.restart_now_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.restart_now_button.clicked.connect(self.accept)
        button_layout.addWidget(self.restart_now_button)
        
        self.restart_later_button = QPushButton("Restart Later")
        self.restart_later_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.restart_later_button.clicked.connect(self.reject)
        button_layout.addWidget(self.restart_later_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()

class DownloadDialog(QDialog):
    def __init__(self, emulator_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Emulator Not Found")
        self.setFixedSize(300, 120)
        self.setModal(True)
        self.setStyleSheet("background-color: #0E5053;")
        
        layout = QVBoxLayout(self)
        
        self.message_label = QLabel(f"{emulator_name} is not installed. Please download it to proceed.")
        self.message_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        button_layout = QHBoxLayout()
        
        self.download_now_button = QPushButton("Download Now")
        self.download_now_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.download_now_button.clicked.connect(self.accept)
        button_layout.addWidget(self.download_now_button)
        
        self.download_later_button = QPushButton("Download Later")
        self.download_later_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.download_later_button.clicked.connect(self.reject)
        button_layout.addWidget(self.download_later_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()

class UpdateDialog(QDialog):
    def __init__(self, current_version, latest_version, release_notes, download_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedSize(350, 200)
        self.setModal(True)
        self.setStyleSheet("background-color: #0E5053;")

        layout = QVBoxLayout(self)

        message = f"Current Version: {current_version}\nLatest Version: {latest_version}\n\nRelease Notes:\n{release_notes}"
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("font-size: 14px; color: white;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        button_layout = QHBoxLayout()
        self.download_button = QPushButton("Download Now")
        self.download_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.download_button.clicked.connect(self.accept)
        button_layout.addWidget(self.download_button)

        self.later_button = QPushButton("Later")
        self.later_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.later_button.clicked.connect(self.reject)
        button_layout.addWidget(self.later_button)

        layout.addLayout(button_layout)
        layout.addStretch()