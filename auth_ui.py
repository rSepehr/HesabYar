# file: auth_ui.py
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QStackedWidget,
)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QPixmap
from dialogs.recovery_dialog import RecoveryDialog
from utils import resource_path


class LoginWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_label = QLabel(self)
        pixmap = QPixmap(resource_path("assets/logo_menu.png"))
        logo_label.setPixmap(
            pixmap.scaled(
                250,
                250,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        title = QLabel("ورود به حساب کاربری", self)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("نام کاربری")

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("رمز عبور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("ورود", self)
        self.login_button.setObjectName("primaryButton")
        self.login_button.setFixedHeight(40)

        self.username_input.returnPressed.connect(self.login_button.click)
        self.password_input.returnPressed.connect(self.login_button.click)

        self.forgot_password_button = QPushButton("رمز عبور را فراموش کرده‌ام", self)
        self.forgot_password_button.setObjectName("linkButton")

        switch_layout = QHBoxLayout()
        switch_label = QLabel("حساب کاربری ندارید؟", self)
        self.signup_switch_button = QPushButton("ثبت نام کنید", self)
        self.signup_switch_button.setObjectName("linkButton")
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.signup_switch_button)

        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.forgot_password_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.login_button)
        layout.addLayout(switch_layout)


class SignupWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_label = QLabel(self)
        pixmap = QPixmap(resource_path("assets/logo_menu.png"))
        logo_label.setPixmap(
            pixmap.scaled(
                128,
                128,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        title = QLabel("ایجاد حساب کاربری جدید", self)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("نام کاربری")

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("ایمیل")

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("رمز عبور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_password_input = QLineEdit(self)
        self.confirm_password_input.setPlaceholderText("تکرار رمز عبور")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.secret_question_input = QLineEdit(self)
        self.secret_question_input.setPlaceholderText(
            "سوال امنیتی (مثال: نام اولین معلم؟)"
        )

        self.secret_answer_input = QLineEdit(self)
        self.secret_answer_input.setPlaceholderText("پاسخ سوال امنیتی")
        self.secret_answer_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.signup_button = QPushButton("ثبت نام", self)
        self.signup_button.setObjectName("primaryButton")
        self.signup_button.setFixedHeight(40)

        switch_layout = QHBoxLayout()
        switch_label = QLabel("قبلاً ثبت نام کرده‌اید؟", self)
        self.login_switch_button = QPushButton("وارد شوید", self)
        self.login_switch_button.setObjectName("linkButton")
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.login_switch_button)

        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(self.secret_question_input)
        layout.addWidget(self.secret_answer_input)
        layout.addWidget(self.signup_button)
        layout.addLayout(switch_layout)


class AuthWindow(QMainWindow):
    login_successful = Signal()

    def __init__(self, db_manager):
        super().__init__()
        self.setWindowTitle("سیستم حسابداری")
        self.setFixedSize(500, 750)
        self.db_manager = db_manager

        self.stacked_widget = QStackedWidget(self)
        self.login_widget = LoginWidget()
        self.signup_widget = SignupWidget()

        self.stacked_widget.addWidget(self.login_widget)
        self.stacked_widget.addWidget(self.signup_widget)

        central_widget = QWidget(self, objectName="centralWidget")
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.stacked_widget)
        self.setCentralWidget(central_widget)

        self.login_widget.signup_switch_button.clicked.connect(self.go_to_signup_page)
        self.signup_widget.login_switch_button.clicked.connect(self.go_to_login_page)
        self.login_widget.login_button.clicked.connect(self.handle_login)
        self.signup_widget.signup_button.clicked.connect(self.handle_signup)
        self.login_widget.forgot_password_button.clicked.connect(
            self.handle_forgot_password
        )

        self.load_last_user()

    def load_last_user(self):
        settings = QSettings("MySoft", "HesabYar")
        last_username = settings.value("last_username", "")
        if last_username:
            self.login_widget.username_input.setText(last_username)
            self.login_widget.password_input.setFocus()

    def save_last_user(self, username):
        settings = QSettings("MySoft", "HesabYar")
        settings.setValue("last_username", username)

    def go_to_signup_page(self):
        self.stacked_widget.setCurrentIndex(1)
        self.setWindowTitle("ثبت نام")

    def go_to_login_page(self):
        self.stacked_widget.setCurrentIndex(0)
        self.setWindowTitle("ورود")

    def handle_login(self):
        username = self.login_widget.username_input.text()
        password = self.login_widget.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "خطا", "نام کاربری و رمز عبور نباید خالی باشند.")
            return

        success, message = self.db_manager.check_user_credentials(username, password)
        if success:
            self.save_last_user(username)
            self.login_successful.emit()
            self.close()
        else:
            QMessageBox.critical(self, "خطا در ورود", message)

    def handle_signup(self):
        username = self.signup_widget.username_input.text().strip()
        email = self.signup_widget.email_input.text().strip()
        password = self.signup_widget.password_input.text()
        confirm_password = self.signup_widget.confirm_password_input.text()
        secret_question = self.signup_widget.secret_question_input.text().strip()
        secret_answer = self.signup_widget.secret_answer_input.text()

        if not all(
            [
                username,
                email,
                password,
                confirm_password,
                secret_question,
                secret_answer,
            ]
        ):
            QMessageBox.warning(self, "خطا", "لطفاً تمام فیلدها را پر کنید.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "خطا", "رمزهای عبور با هم مطابقت ندارند.")
            return

        success, msg, new_id = self.db_manager.add_user(
            username, email, password, secret_question, secret_answer
        )

        if success:
            QMessageBox.information(self, "موفق", f"{msg}\nحالا می‌توانید وارد شوید.")
            self.go_to_login_page()
        else:
            QMessageBox.critical(self, "خطا در ثبت نام", msg)

    def handle_forgot_password(self):
        dialog = RecoveryDialog(self.db_manager, self)
        dialog.exec()
