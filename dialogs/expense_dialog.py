# file: dialogs/expense_dialog.py
import jdatetime
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
from PySide6.QtCore import Qt
from signal_bus import signal_bus


class ExpenseDialog(QDialog):
    def __init__(self, db_manager, expense_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.expense_id = expense_id

        self.setObjectName("formDialog")
        window_title = "ویرایش هزینه" if self.expense_id else "افزودن هزینه جدید"
        self.setWindowTitle(window_title)
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.description_input = QLineEdit(
            placeholderText="مثال: پرداخت قبض اینترنت ماهانه"
        )
        self.amount_input = QLineEdit(placeholderText="مبلغ به ریال")
        self.date_input = QLineEdit(jdatetime.date.today().strftime("%Y/%m/%d"))

        self.account_combo = QComboBox()

        form_layout.addRow("شرح هزینه:", self.description_input)
        form_layout.addRow("مبلغ (ریال):", self.amount_input)
        form_layout.addRow("تاریخ:", self.date_input)
        form_layout.addRow("حساب هزینه مربوطه:", self.account_combo)

        layout.addLayout(form_layout)

        button_box = QHBoxLayout()
        save_btn = QPushButton("ذخیره", objectName="primaryButton", clicked=self.accept)
        cancel_btn = QPushButton("لغو", clicked=self.reject)
        button_box.addStretch()
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)

        self.load_expense_accounts()

        if self.expense_id:
            self.load_expense_data()

    def load_expense_accounts(self):
        """لیست حساب‌های نوع هزینه را بارگذاری می‌کند."""
        expense_accounts = self.db_manager.get_accounts_by_type("expense")
        for acc in expense_accounts:
            self.account_combo.addItem(acc["name"], userData=acc["id"])

    def load_expense_data(self):
        expense = self.db_manager.get_expense_by_id(self.expense_id)
        if expense:
            self.description_input.setText(expense["description"])
            self.amount_input.setText(str(int(expense["amount"])))
            self.date_input.setText(expense["expense_date"])

            account_id = (
                expense["account_id"] if "account_id" in expense.keys() else None
            )
            if account_id:
                index = self.account_combo.findData(account_id)
                if index != -1:
                    self.account_combo.setCurrentIndex(index)

    def accept(self):
        description = self.description_input.text().strip()
        amount_text = self.amount_input.text().strip()
        expense_date = self.date_input.text().strip()
        account_id = self.account_combo.currentData()

        if not all([description, amount_text, account_id]):
            QMessageBox.warning(self, "خطا", "شرح، مبلغ و حساب هزینه الزامی هستند.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "خطا", "لطفاً برای مبلغ یک عدد معتبر وارد کنید.")
            return

        if self.expense_id:
            success, msg = self.db_manager.update_expense(
                self.expense_id, description, amount, expense_date, None, account_id
            )
        else:
            success, msg = self.db_manager.add_expense(
                description, amount, expense_date, None, account_id
            )

        if success:
            signal_bus.expense_saved.emit()
            QMessageBox.information(self, "موفقیت", msg)
            super().accept()
        else:
            QMessageBox.critical(self, "خطا", msg)
