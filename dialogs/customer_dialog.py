# file: dialogs/customer_dialog.py
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
from PySide6.QtCore import Qt, Signal
from dialogs.custom_message_box import CustomMessageBox
from signal_bus import signal_bus


class CustomerDialog(QDialog):
    data_saved = Signal(int)

    def __init__(self, db_manager, customer_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.customer_id = customer_id

        self.setObjectName("formDialog")
        window_title = "ویرایش مشتری" if self.customer_id else "افزودن مشتری جدید"
        self.setWindowTitle(window_title)
        self.setMinimumWidth(450)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        title_label = QLabel(
            window_title,
            self,
            objectName="dialogTitleLabel",
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        main_layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit(placeholderText="نام شخص حقیقی یا حقوقی")
        self.national_id_input = QLineEdit(placeholderText="کد ملی یا شناسه ملی")
        self.economic_code_input = QLineEdit(placeholderText="اختیاری")
        self.email_input = QLineEdit(placeholderText="اختیاری")
        self.phone_input = QLineEdit(placeholderText="اختیاری")
        self.address_input = QLineEdit(placeholderText="اختیاری")
        self.postal_code_input = QLineEdit(placeholderText="اختیاری")

        form_layout.addRow("نام:", self.name_input)
        form_layout.addRow("کد/شناسه ملی:", self.national_id_input)
        form_layout.addRow("کد اقتصادی:", self.economic_code_input)
        form_layout.addRow("ایمیل:", self.email_input)
        form_layout.addRow("تلفن:", self.phone_input)
        form_layout.addRow("آدرس:", self.address_input)
        form_layout.addRow("کد پستی:", self.postal_code_input)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        button_layout = QHBoxLayout()
        self.save_button = QPushButton(
            "ذخیره", self, objectName="primaryButton", clicked=self.accept
        )
        self.cancel_button = QPushButton(
            "لغو", self, objectName="cancelButton", clicked=self.reject
        )
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        if self.customer_id:
            self.load_customer_data()

    def load_customer_data(self):
        customer_data = self.db_manager.get_customer_by_id(self.customer_id)
        if customer_data:
            self.name_input.setText(customer_data[1])
            self.email_input.setText(customer_data[2] or "")
            self.phone_input.setText(customer_data[3] or "")
            self.address_input.setText(customer_data[4] or "")
            self.national_id_input.setText(customer_data[5] or "")
            self.economic_code_input.setText(customer_data[6] or "")
            self.postal_code_input.setText(customer_data[7] or "")

    def accept(self):
        name = self.name_input.text().strip()
        national_id = self.national_id_input.text().strip()
        economic_code = self.economic_code_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()
        postal_code = self.postal_code_input.text().strip()

        if not name or not national_id:
            QMessageBox.warning(self, "خطا", "نام و کد/شناسه ملی نمی‌توانند خالی باشند.")
            return

        if name or email or phone:
            duplicates = self.db_manager.check_for_duplicates(
                name, email, phone, self.customer_id
            )
            if duplicates:
                msg = "یک یا چند مورد با اطلاعات مشابه یافت شد:\n"
                for dup in duplicates:
                    if dup[0].lower() == name.lower():
                        msg += f"\n- نام '{name}' از قبل برای مشتری دیگری ثبت شده است."
                    if email and dup[1] == email:
                        msg += (
                            f"\n- ایمیل '{email}' از قبل برای مشتری دیگری ثبت شده است."
                        )
                    if phone and dup[2] == phone:
                        msg += (
                            f"\n- تلفن '{phone}' از قبل برای مشتری دیگری ثبت شده است."
                        )
                msg += "\n\nآیا می‌خواهید با این وجود مشتری را ذخیره کنید؟"
                confirm_dialog = CustomMessageBox("هشدار اطلاعات تکراری", msg, self)
                if confirm_dialog.exec() != QMessageBox.StandardButton.Yes:
                    return

        if self.customer_id:
            success, msg = self.db_manager.update_customer(
                self.customer_id,
                name,
                email,
                phone,
                address,
                national_id,
                economic_code,
                postal_code,
            )
            if success:
                signal_bus.customer_saved.emit(self.customer_id)
                super().accept()
        else:
            success, msg, new_id = self.db_manager.add_customer(
                name, email, phone, address, national_id, economic_code, postal_code
            )
            if success:
                signal_bus.customer_saved.emit(new_id)
                super().accept()

        if not success:
            QMessageBox.critical(self, "خطا", msg)
