# file: dialogs/recovery_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QWidget,
)
from PySide6.QtCore import Qt


class RecoveryDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.username = None

        self.setWindowTitle("بازیابی رمز عبور")
        self.setObjectName("formDialog")
        self.setMinimumWidth(450)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget(self)
        main_layout.addWidget(self.stacked_widget)

        self.create_username_page()
        self.create_reset_page()

    def create_username_page(self):
        """صفحه اول: دریافت نام کاربری"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        title = QLabel("بازیابی رمز عبور", objectName="dialogTitleLabel")
        description = QLabel(
            "لطفاً نام کاربری خود را برای شروع فرآیند بازیابی وارد کنید.", wordWrap=True
        )

        self.username_input = QLineEdit(placeholderText="نام کاربری")
        self.next_button = QPushButton("مرحله بعد", objectName="primaryButton")
        self.next_button.clicked.connect(self.process_username_step)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.username_input)
        layout.addWidget(self.next_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.stacked_widget.addWidget(page)

    def create_reset_page(self):
        """صفحه دوم: نمایش سوال، دریافت پاسخ و رمز جدید"""
        page = QWidget()
        layout = QVBoxLayout(page)
        form_layout = QFormLayout()
        layout.setSpacing(15)

        title = QLabel("پاسخ به سوال امنیتی", objectName="dialogTitleLabel")
        self.question_label = QLabel("سوال امنیتی شما در اینجا نمایش داده می‌شود.")
        self.question_label.setStyleSheet("font-weight: bold;")
        self.question_label.setWordWrap(True)

        self.answer_input = QLineEdit(placeholderText="پاسخ سوال امنیتی")
        self.new_password_input = QLineEdit(
            echoMode=QLineEdit.EchoMode.Password, placeholderText="رمز عبور جدید"
        )
        self.confirm_password_input = QLineEdit(
            echoMode=QLineEdit.EchoMode.Password, placeholderText="تکرار رمز عبور جدید"
        )

        form_layout.addRow(self.question_label)
        form_layout.addRow("پاسخ شما:", self.answer_input)
        form_layout.addRow("رمز جدید:", self.new_password_input)
        form_layout.addRow("تکرار رمز:", self.confirm_password_input)

        self.reset_button = QPushButton("بازنشانی رمز عبور", objectName="primaryButton")
        self.reset_button.clicked.connect(self.process_reset_step)

        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addWidget(self.reset_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.stacked_widget.addWidget(page)

    def process_username_step(self):
        """مرحله اول را پردازش کرده و در صورت صحت به مرحله دوم می‌رود."""
        self.username = self.username_input.text().strip()
        if not self.username:
            QMessageBox.warning(self, "خطا", "نام کاربری نمی‌تواند خالی باشد.")
            return

        secret_question = self.db_manager.get_secret_question(self.username)
        if secret_question:
            self.question_label.setText(secret_question)
            self.stacked_widget.setCurrentIndex(1)
        else:
            QMessageBox.critical(
                self,
                "خطا",
                "کاربری با این نام یافت نشد یا سوال امنیتی برای آن تنظیم نشده است.",
            )

    def process_reset_step(self):
        """مرحله دوم را پردازش کرده و در صورت صحت، رمز را ریست می‌کند."""
        answer = self.answer_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not all([answer, new_password, confirm_password]):
            QMessageBox.warning(self, "خطا", "لطفاً تمام فیلدها را پر کنید.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "خطا", "رمزهای عبور جدید با هم مطابقت ندارند.")
            return

        if self.db_manager.check_secret_answer(self.username, answer):
            success, msg = self.db_manager.reset_password(self.username, new_password)
            if success:
                QMessageBox.information(self, "موفقیت", msg)
                self.accept()
            else:
                QMessageBox.critical(self, "خطا", msg)
        else:
            QMessageBox.critical(self, "خطا", "پاسخ سوال امنیتی اشتباه است.")
