# file: dialogs/account_dialog.py
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


class AccountDialog(QDialog):
    def __init__(self, db_manager, account_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.account_id = account_id

        self.setWindowTitle("افزودن / ویرایش حساب")
        self.setObjectName("formDialog")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItem("درآمد", "income")
        self.type_combo.addItem("هزینه", "expense")
        self.description_input = QTextEdit()

        form_layout.addRow("نام حساب:", self.name_input)
        form_layout.addRow("نوع حساب:", self.type_combo)
        form_layout.addRow("توضیحات:", self.description_input)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("ذخیره", objectName="primaryButton", clicked=self.accept)
        cancel_btn = QPushButton("لغو", clicked=self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        if self.account_id:
            self.load_account_data()

    def load_account_data(self):
        account = self.db_manager.get_account_by_id(self.account_id)
        if account:
            self.name_input.setText(account["name"])
            index = self.type_combo.findData(account["type"])
            if index != -1:
                self.type_combo.setCurrentIndex(index)
            self.description_input.setPlainText(account["description"])

    def accept(self):
        name = self.name_input.text().strip()
        acc_type = self.type_combo.currentData()
        description = self.description_input.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "خطا", "نام حساب نمی‌تواند خالی باشد.")
            return

        if self.account_id:
            success, msg = self.db_manager.update_account(
                self.account_id, name, acc_type, description
            )
        else:
            success, msg = self.db_manager.add_account(name, acc_type, description)

        if success:
            QMessageBox.information(self, "موفقیت", msg)
            super().accept()
        else:
            QMessageBox.critical(self, "خطا", msg)
