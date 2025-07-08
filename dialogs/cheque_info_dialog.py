# file: dialogs/cheque_info_dialog.py
import jdatetime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
)


class ChequeInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ورود اطلاعات چک")
        self.setObjectName("formDialog")
        self.setModal(True)
        self.setMinimumWidth(350)

        self.data = None

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.cheque_number_input = QLineEdit()
        self.bank_name_input = QLineEdit()
        self.due_date_input = QLineEdit(jdatetime.date.today().strftime("%Y/%m/%d"))

        form_layout.addRow("شماره چک:", self.cheque_number_input)
        form_layout.addRow("نام بانک:", self.bank_name_input)
        form_layout.addRow("تاریخ سررسید:", self.due_date_input)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("تایید", objectName="primaryButton", clicked=self.accept)
        cancel_btn = QPushButton("لغو", clicked=self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def accept(self):
        """داده‌ها را قبل از بستن دیالوگ جمع‌آوری می‌کند."""
        if not self.cheque_number_input.text().strip():
            return

        self.data = {
            "number": self.cheque_number_input.text().strip(),
            "bank": self.bank_name_input.text().strip(),
            "due_date": self.due_date_input.text().strip(),
        }
        super().accept()

    def get_data(self):
        """این متد داده‌های جمع‌آوری شده را برمی‌گرداند."""
        return self.data
