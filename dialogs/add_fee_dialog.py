# file: dialogs/add_fee_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QHBoxLayout,
    QPushButton,
    QComboBox,
)
from PySide6.QtCore import QSettings


class AddFeeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("افزودن هزینه/کارمزد")
        self.setObjectName("formDialog")
        self.setMinimumWidth(350)

        self.fee_data = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.description_combo = QComboBox()
        self.description_combo.setEditable(True)
        self.description_combo.setPlaceholderText("شرح هزینه را تایپ یا انتخاب کنید")

        self.amount_input = QLineEdit("0")

        form.addRow("شرح هزینه:", self.description_combo)
        form.addRow("مبلغ (ریال):", self.amount_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        save_btn = QPushButton(
            "افزودن", objectName="primaryButton", clicked=self.accept
        )
        cancel_btn = QPushButton("لغو", clicked=self.reject)
        buttons.addStretch()
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.load_fee_names()

    def load_fee_names(self):
        settings = QSettings("MySoft", "HesabYar")
        custom_fees = settings.value("financial/custom_fees", [])
        if custom_fees:
            if isinstance(custom_fees, str):
                custom_fees = [custom_fees]
            self.description_combo.addItems(custom_fees)

    def accept(self):
        description = self.description_combo.currentText().strip()
        amount_text = self.amount_input.text().strip()

        if not description or not amount_text:
            QMessageBox.warning(self, "خطا", "شرح و مبلغ نمی‌توانند خالی باشند.")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                QMessageBox.warning(self, "خطا", "مبلغ باید یک عدد مثبت باشد.")
                return
        except ValueError:
            QMessageBox.warning(self, "خطا", "لطفاً برای مبلغ یک عدد معتبر وارد کنید.")
            return

        self.fee_data = {"description": description, "amount": amount}
        super().accept()

    def get_fee_data(self):
        return self.fee_data
