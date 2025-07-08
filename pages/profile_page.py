# file: pages/profile_page.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QAction
from db_manager import DatabaseManager
from utils import resource_path


class ProfilePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.current_username = ""

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setSpacing(20)

        profile_frame = QFrame(objectName="formDialog")
        layout = QVBoxLayout(profile_frame)
        title = QLabel("پروفایل کاربری", objectName="dialogTitleLabel")
        layout.addWidget(title)
        form_layout = QFormLayout()
        self.username_label = QLabel()
        self.email_label = QLabel()
        form_layout.addRow("نام کاربری:", self.username_label)
        form_layout.addRow("ایمیل:", self.email_label)
        layout.addLayout(form_layout)

        main_layout.addWidget(profile_frame)

        change_pass_frame = QFrame(objectName="formDialog")
        cp_layout = QVBoxLayout(change_pass_frame)
        cp_title = QLabel("تغییر رمز عبور", objectName="dialogTitleLabel")
        cp_layout.addWidget(cp_title)
        change_pass_form = QFormLayout()
        self.current_password_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.new_password_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.confirm_password_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.setup_password_visibility_action(self.current_password_input)
        self.setup_password_visibility_action(self.new_password_input)
        self.setup_password_visibility_action(self.confirm_password_input)
        change_pass_form.addRow("رمز عبور فعلی:", self.current_password_input)
        change_pass_form.addRow("رمز عبور جدید:", self.new_password_input)
        change_pass_form.addRow("تکرار رمز عبور جدید:", self.confirm_password_input)
        cp_layout.addLayout(change_pass_form)
        self.change_password_button = QPushButton(
            "تغییر رمز عبور", objectName="primaryButton"
        )
        self.change_password_button.clicked.connect(self.handle_change_password)
        cp_layout.addWidget(self.change_password_button, 0, Qt.AlignmentFlag.AlignLeft)

        main_layout.addWidget(change_pass_frame)

        security_frame = QFrame(objectName="formDialog")
        sq_layout = QVBoxLayout(security_frame)
        sq_title = QLabel("مدیریت سوال امنیتی", objectName="dialogTitleLabel")
        sq_layout.addWidget(sq_title)
        security_form = QFormLayout()
        self.secret_question_input = QLineEdit(
            placeholderText="سوال امنیتی خود را وارد یا ویرایش کنید"
        )
        self.secret_answer_input = QLineEdit(
            echoMode=QLineEdit.EchoMode.Password,
            placeholderText="پاسخ جدید را برای ذخیره وارد کنید",
        )
        self.setup_password_visibility_action(self.secret_answer_input)
        security_form.addRow("سوال امنیتی:", self.secret_question_input)
        security_form.addRow("پاسخ امنیتی:", self.secret_answer_input)
        sq_layout.addLayout(security_form)
        self.save_security_button = QPushButton(
            "ذخیره سوال امنیتی", objectName="primaryButton"
        )
        self.save_security_button.clicked.connect(self.handle_save_security_question)
        sq_layout.addWidget(self.save_security_button, 0, Qt.AlignmentFlag.AlignLeft)

        main_layout.addWidget(security_frame)
        main_layout.addStretch()

    def setup_password_visibility_action(self, line_edit):
        action = QAction(
            QIcon(resource_path("assets/icons/eye.svg")), "Show/Hide Password", self
        )
        action.setCheckable(True)
        action.toggled.connect(
            lambda checked: line_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        line_edit.addAction(action, QLineEdit.ActionPosition.LeadingPosition)

    def load_user_data(self):
        """اطلاعات کاربر و سوال امنیتی او را بارگذاری می‌کند."""
        settings = QSettings("MySoft", "HesabYar")
        self.current_username = settings.value("last_username", "")
        if self.current_username:
            user_info = self.db_manager.get_user_info(self.current_username)
            if user_info:
                self.username_label.setText(f"<b>{user_info['username']}</b>")
                self.email_label.setText(user_info["email"])

            secret_question = self.db_manager.get_secret_question(self.current_username)
            if secret_question:
                self.secret_question_input.setText(secret_question)

        self.current_password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()
        self.secret_answer_input.clear()

    def handle_change_password(self):
        current_pass = self.current_password_input.text()
        new_pass = self.new_password_input.text()
        confirm_pass = self.confirm_password_input.text()

        if not all([current_pass, new_pass, confirm_pass]):
            QMessageBox.warning(
                self, "خطا", "تمام فیلدهای تغییر رمز عبور باید پر شوند."
            )
            return

        if new_pass != confirm_pass:
            QMessageBox.warning(
                self, "خطا", "رمز عبور جدید و تکرار آن با هم مطابقت ندارند."
            )
            return

        if len(new_pass) < 6:
            QMessageBox.warning(self, "خطا", "رمز عبور جدید باید حداقل ۶ کاراکتر باشد.")
            return

        success, msg = self.db_manager.change_password(
            self.current_username, current_pass, new_pass
        )
        if success:
            QMessageBox.information(self, "موفقیت", msg)
            self.current_password_input.clear()
            self.new_password_input.clear()
            self.confirm_password_input.clear()
        else:
            QMessageBox.critical(self, "خطا", msg)

    def handle_save_security_question(self):
        """سوال و جواب امنیتی جدید را در دیتابیس ذخیره می‌کند."""
        question = self.secret_question_input.text().strip()
        answer = self.secret_answer_input.text()

        if not question or not answer:
            QMessageBox.warning(self, "خطا", "سوال و جواب امنیتی نمی‌توانند خالی باشند.")
            return

        reply = QMessageBox.question(
            self, "تایید", "آیا از تغییر سوال و جواب امنیتی خود مطمئن هستید؟"
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.db_manager.update_security_question(
                self.current_username, question, answer
            )
            if success:
                QMessageBox.information(self, "موفقیت", msg)
                self.secret_answer_input.clear()
            else:
                QMessageBox.critical(self, "خطا", msg)
