# file: dialogs/payment_dialog.py
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
from PySide6.QtCore import Qt
from signal_bus import signal_bus


class PaymentDialog(QDialog):
    def __init__(self, db_manager, invoice_id, remaining_balance, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.invoice_id = invoice_id

        self.setObjectName("formDialog")
        self.setWindowTitle("ثبت پرداخت جدید")
        self.setMinimumWidth(350)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        form_layout = QFormLayout()

        remaining_label = QLabel(f"{remaining_balance:,.0f} ریال")
        remaining_label.setStyleSheet("font-weight: bold; color: #e74c3c;")

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("مبلغ پرداختی جدید به ریال")
        self.amount_input.setText(str(int(remaining_balance)))

        form_layout.addRow("مبلغ باقی‌مانده:", remaining_label)
        form_layout.addRow("مبلغ پرداختی جدید:", self.amount_input)

        layout.addLayout(form_layout)

        button_box = QHBoxLayout()
        save_btn = QPushButton(
            "ثبت پرداخت", objectName="primaryButton", clicked=self.accept
        )
        cancel_btn = QPushButton("لغو", clicked=self.reject)
        button_box.addStretch()
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)

        layout.addLayout(button_box)

    def accept(self):
        amount_text = self.amount_input.text().strip()
        if not amount_text:
            QMessageBox.warning(self, "خطا", "مبلغ پرداختی نمی‌تواند خالی باشد.")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                QMessageBox.warning(self, "خطا", "مبلغ پرداختی باید یک عدد مثبت باشد.")
                return
        except ValueError:
            QMessageBox.warning(self, "خطا", "لطفاً برای مبلغ یک عدد معتبر وارد کنید.")
            return

        success, msg = self.db_manager.add_payment(self.invoice_id, amount)

        if success:
            signal_bus.invoice_saved.emit()
            QMessageBox.information(self, "موفقیت", msg)
            super().accept()
        else:
            QMessageBox.critical(self, "خطا", msg)
