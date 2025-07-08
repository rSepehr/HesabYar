# file: dialogs/custom_message_box.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class CustomMessageBox(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setObjectName("confirmDialog")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        self.message_label = QLabel(message, self)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.yes_button = QPushButton(
            "بله", self, objectName="confirmButton", clicked=self.accept
        )
        self.no_button = QPushButton(
            "خیر", self, objectName="cancelButton", clicked=self.reject
        )
        self.close_button = QPushButton("بستن", self)
        self.close_button.setVisible(False)

        self.close_button.clicked.connect(lambda: self.done(2))

        button_layout.addStretch()
        button_layout.addWidget(self.yes_button)
        button_layout.addWidget(self.no_button)
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
