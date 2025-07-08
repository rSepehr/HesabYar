# file: dialogs/pdf_success_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from utils import resource_path


class PdfSuccessDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("موفقیت")
        self.setModal(True)
        self.setObjectName("confirmDialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        icon_label = QLabel(self)
        icon_label.setPixmap(
            QIcon(resource_path("assets/icons/check-circle.svg")).pixmap(48, 48)
        )
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message_label = QLabel(
            message, self, alignment=Qt.AlignmentFlag.AlignCenter, wordWrap=True
        )

        layout.addWidget(icon_label)
        layout.addWidget(message_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.OpenFile = 1
        self.OpenFolder = 2

        open_file_btn = QPushButton(
            " باز کردن فایل", clicked=lambda: self.done(self.OpenFile)
        )
        open_file_btn.setIcon(QIcon(resource_path("assets/icons/file-text.svg")))

        open_folder_btn = QPushButton(
            " باز کردن پوشه", clicked=lambda: self.done(self.OpenFolder)
        )
        open_folder_btn.setIcon(QIcon(resource_path("assets/icons/folder.svg")))

        close_btn = QPushButton(" بستن", clicked=self.reject)
        close_btn.setObjectName("cancelButton")

        button_layout.addStretch()
        button_layout.addWidget(open_file_btn)
        button_layout.addWidget(open_folder_btn)
        button_layout.addWidget(close_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)
