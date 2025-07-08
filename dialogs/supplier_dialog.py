# file: dialogs/supplier_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from signal_bus import signal_bus


class SupplierDialog(QDialog):
    def __init__(self, db_manager, supplier_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.supplier_id = supplier_id

        self.setObjectName("formDialog")
        window_title = (
            "ویرایش تامین‌کننده" if self.supplier_id else "افزودن تامین‌کننده جدید"
        )
        self.setWindowTitle(window_title)
        self.setMinimumWidth(450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(window_title, objectName="dialogTitleLabel"))

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()
        self.national_id_input = QLineEdit()
        self.economic_code_input = QLineEdit()
        self.postal_code_input = QLineEdit()

        form_layout.addRow("نام شرکت/شخص:", self.name_input)
        form_layout.addRow("کد/شناسه ملی:", self.national_id_input)
        form_layout.addRow("کد اقتصادی:", self.economic_code_input)
        form_layout.addRow("تلفن:", self.phone_input)
        form_layout.addRow("ایمیل:", self.email_input)
        form_layout.addRow("کد پستی:", self.postal_code_input)
        form_layout.addRow("آدرس:", self.address_input)
        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("ذخیره", objectName="primaryButton", clicked=self.accept)
        cancel_btn = QPushButton("لغو", clicked=self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        if self.supplier_id:
            self.load_supplier_data()

    def load_supplier_data(self):
        data = self.db_manager.get_supplier_by_id(self.supplier_id)
        if data:
            self.name_input.setText(data["name"])
            self.email_input.setText(data["email"] or "")
            self.phone_input.setText(data["phone"] or "")
            self.address_input.setText(data["address"] or "")
            self.national_id_input.setText(data["national_id"] or "")
            self.economic_code_input.setText(data["economic_code"] or "")
            self.postal_code_input.setText(data["postal_code"] or "")

    def accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام تامین‌کننده نمی‌تواند خالی باشد.")
            return

        data = {
            "name": name,
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.text().strip(),
            "national_id": self.national_id_input.text().strip(),
            "economic_code": self.economic_code_input.text().strip(),
            "postal_code": self.postal_code_input.text().strip(),
        }

        if self.supplier_id:
            success, msg = self.db_manager.update_supplier(self.supplier_id, **data)
        else:
            success, msg, _ = self.db_manager.add_supplier(**data)

        if success:
            signal_bus.supplier_saved.emit()
            QMessageBox.information(self, "موفقیت", msg)
            super().accept()
        else:
            QMessageBox.critical(self, "خطا", msg)
