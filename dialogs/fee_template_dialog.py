# file: dialogs/fee_template_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QLabel,
)
from PySide6.QtCore import Qt


class FeeTemplateDialog(QDialog):
    """
    این دیالوگ فرمی برای افزودن یا ویرایش قالب‌های هزینه (مانند مالیات، کارمزد و...) فراهم می‌کند.
    """

    def __init__(self, db_manager, fee_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.fee_id = fee_id

        self.setWindowTitle("افزودن/ویرایش قالب هزینه")
        self.setObjectName("formDialog")
        self.setMinimumWidth(400)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: ارزش افزوده، هزینه بسته‌بندی")

        self.type_combo = QComboBox()
        self.type_combo.addItems(["درصدی (%)", "مبلغ ثابت"])

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("مقدار عددی (مثال: 9 یا 50000)")

        form_layout.addRow("نام هزینه:", self.name_input)
        form_layout.addRow("نوع هزینه:", self.type_combo)
        form_layout.addRow("مقدار پیش‌فرض:", self.value_input)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("ذخیره", objectName="primaryButton")
        self.cancel_button = QPushButton("لغو")

        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        if self.fee_id:
            self.load_fee_data()

    def load_fee_data(self):
        """داده‌های یک قالب هزینه را برای ویرایش در فرم بارگذاری می‌کند."""
        template = self.db_manager.get_fee_template_by_id(self.fee_id)
        if template:
            self.name_input.setText(template["name"])
            self.value_input.setText(str(template["value"]))
            if template["type"] == "percent":
                self.type_combo.setCurrentIndex(0)
            else:
                self.type_combo.setCurrentIndex(1)

    def accept(self):
        """داده‌ها را اعتبارسنجی کرده و در دیتابیس ذخیره می‌کند."""
        name = self.name_input.text().strip()
        value_text = self.value_input.text().strip()
        fee_type = "percent" if self.type_combo.currentIndex() == 0 else "amount"

        if not name or not value_text:
            QMessageBox.warning(self, "خطا", "نام و مقدار هزینه نمی‌توانند خالی باشند.")
            return

        try:
            value = float(value_text)
        except ValueError:
            QMessageBox.warning(self, "خطا", "لطفاً برای مقدار یک عدد معتبر وارد کنید.")
            return

        if self.fee_id:
            success, msg = self.db_manager.update_fee_template(
                self.fee_id, name, fee_type, value
            )
        else:
            success, msg = self.db_manager.add_fee_template(name, fee_type, value)

        if success:
            QMessageBox.information(self, "موفق", msg)
            super().accept()
        else:
            QMessageBox.critical(self, "خطا", msg)
