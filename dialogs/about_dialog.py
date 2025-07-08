# file: dialogs/about_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from utils import resource_path


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("درباره حساب‌یار")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 20, 0, 20)

        self.banner_label = QLabel(self)
        self.banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(resource_path("assets/images/about_banner.png"))
        if not pixmap.isNull():
            self.banner_label.setPixmap(
                pixmap.scaledToWidth(700, Qt.TransformationMode.SmoothTransformation)
            )
        layout.addWidget(self.banner_label)

        self.info_label = QLabel(self)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setOpenExternalLinks(True)
        self.info_label.setTextFormat(Qt.TextFormat.RichText)

        self.info_label.setText(
            """
    <h2>نرم‌افزار حسابداری «حساب‌یار»</h2>
    <p><b>نسخه ۱.۰</b></p>
    <p>طراحی و توسعه توسط: <b>سپهر عبقری</b></p>
    <hr>
    <p>«حساب‌یار» یک نرم‌افزار حسابداری رایگان و متن‌باز است<br>
    که برای حمایت از کسب‌وکارهای کوچک و متوسط ایرانی ساخته شده.</p>
    <p>این پروژه با تمرکز بر سادگی، کارایی و دسترسی همگانی<br>
    توسط یک توسعه‌دهنده مستقل ایرانی طراحی و پیاده‌سازی شده است.</p>
    <p style="margin-top: 10px;">
        <a href="https://github.com/rSepehr/HesabYar" target="_blank">مشاهده در GitHub</a> |
        <a href="https://github.com/rSepehr/HesabYar" target="_blank">حمایت مالی</a>
    </p>
    """
        )
        layout.addWidget(self.info_label)

        button_layout = QHBoxLayout()
        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
