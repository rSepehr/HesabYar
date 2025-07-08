# file: dialogs/cheque_dialog.py
import jdatetime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)
from signal_bus import signal_bus


class ChequeDialog(QDialog):
    def __init__(self, db_manager, cheque_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.cheque_id = cheque_id

        self.setWindowTitle("ثبت / ویرایش چک")
        self.setObjectName("formDialog")
        self.setMinimumWidth(450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems(["دریافتی", "پرداختی"])

        self.cheque_number_input = QLineEdit()
        self.bank_name_input = QLineEdit()
        self.amount_input = QLineEdit()

        today_str = jdatetime.date.today().strftime("%Y/%m/%d")
        self.issue_date_input = QLineEdit(today_str)
        self.due_date_input = QLineEdit(today_str)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["در انتظار وصول", "پاس شده", "برگشتی"])

        self.description_input = QTextEdit()

        form_layout.addRow("نوع چک:", self.type_combo)
        form_layout.addRow("شماره چک:", self.cheque_number_input)
        form_layout.addRow("نام بانک:", self.bank_name_input)
        form_layout.addRow("مبلغ (ریال):", self.amount_input)
        form_layout.addRow("تاریخ صدور:", self.issue_date_input)
        form_layout.addRow("تاریخ سررسید:", self.due_date_input)
        form_layout.addRow("وضعیت:", self.status_combo)
        form_layout.addRow("توضیحات:", self.description_input)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("ذخیره", objectName="primaryButton", clicked=self.accept)
        cancel_btn = QPushButton("لغو", clicked=self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        if self.cheque_id:
            self.load_cheque_data()

    def load_cheque_data(self):
        data = self.db_manager.get_cheque_by_id(self.cheque_id)
        if data:
            self.type_combo.setCurrentText(data["type"])
            self.cheque_number_input.setText(data["cheque_number"])
            self.bank_name_input.setText(data["bank_name"])
            self.amount_input.setText(str(int(data["amount"])))
            self.issue_date_input.setText(data["issue_date"])
            self.due_date_input.setText(data["due_date"])
            self.status_combo.setCurrentText(data["status"])
            self.description_input.setPlainText(data["description"])

    def accept(self):
        amount_text = self.amount_input.text()
        if not self.cheque_number_input.text() or not amount_text:
            QMessageBox.warning(self, "خطا", "شماره چک و مبلغ نمی‌توانند خالی باشند.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "خطا", "مبلغ وارد شده معتبر نیست.")
            return

        data = {
            "type": self.type_combo.currentText(),
            "cheque_number": self.cheque_number_input.text().strip(),
            "bank_name": self.bank_name_input.text().strip(),
            "amount": amount,
            "issue_date": self.issue_date_input.text().strip(),
            "due_date": self.due_date_input.text().strip(),
            "status": self.status_combo.currentText(),
            "description": self.description_input.toPlainText().strip(),
            "invoice_id": None,
        }

        if self.cheque_id:
            success, msg = self.db_manager.update_cheque(self.cheque_id, data)
        else:
            success, msg = self.db_manager.add_cheque(data)

        if success:
            signal_bus.invoice_saved.emit()
            QMessageBox.information(self, "موفقیت", msg)
            super().accept()
        else:
            QMessageBox.critical(self, "خطا", msg)
