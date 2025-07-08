# file: dialogs/product_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QComboBox,
    QDoubleSpinBox,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from signal_bus import signal_bus


class ProductDialog(QDialog):
    def __init__(self, db_manager, product_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.product_id = product_id

        self.setObjectName("formDialog")
        window_title = (
            "ویرایش کالا/خدمات" if self.product_id else "افزودن کالا/خدمات جدید"
        )
        self.setWindowTitle(window_title)
        self.setMinimumWidth(450)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.unit_input = QComboBox()
        self.unit_input.setEditable(True)
        self.unit_price_input = QLineEdit()
        self.stock_quantity_input = QDoubleSpinBox()
        self.stock_quantity_input.setRange(0, 999999999)

        self.account_combo = QComboBox()

        form_layout.addRow("نام کالا/خدمات:", self.name_input)
        form_layout.addRow("واحد شمارش:", self.unit_input)
        form_layout.addRow("قیمت واحد (ریال):", self.unit_price_input)
        form_layout.addRow("موجودی انبار:", self.stock_quantity_input)
        form_layout.addRow("حساب درآمد مربوطه:", self.account_combo)
        form_layout.addRow("توضیحات:", self.description_input)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton(
            "ذخیره", objectName="primaryButton", clicked=self.accept
        )
        self.cancel_button = QPushButton("لغو", clicked=self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.populate_combos()

        if self.product_id:
            self.load_product_data()

    def populate_combos(self):
        income_accounts = self.db_manager.get_accounts_by_type("income")
        for acc in income_accounts:
            self.account_combo.addItem(acc["name"], userData=acc["id"])

        default_units = ["عدد", "بسته", "کیلوگرم", "گرم", "متر", "ساعت", "پروژه"]
        db_units = self.db_manager.get_distinct_units()
        all_units = sorted(list(set(default_units + db_units)))
        self.unit_input.addItems(all_units)

    def load_product_data(self):
        product_data = self.db_manager.get_product_by_id(self.product_id)
        if product_data:
            self.name_input.setText(product_data["name"])
            self.description_input.setPlainText(product_data["description"])
            self.unit_input.setCurrentText(product_data["unit"])
            self.unit_price_input.setText(str(int(product_data["unit_price"])))

            stock_qty = (
                product_data["stock_quantity"]
                if "stock_quantity" in product_data.keys()
                else 0
            )
            self.stock_quantity_input.setValue(stock_qty)

            account_id = (
                product_data["account_id"]
                if "account_id" in product_data.keys()
                else None
            )
            if account_id:
                index = self.account_combo.findData(account_id)
                if index != -1:
                    self.account_combo.setCurrentIndex(index)

    def accept(self):
        name = self.name_input.text().strip()
        account_id = self.account_combo.currentData()

        if not name or not account_id:
            QMessageBox.warning(self, "خطا", "نام کالا و انتخاب حساب درآمد الزامی است.")
            return

        stock_quantity = self.stock_quantity_input.value()
        description = self.description_input.toPlainText().strip()
        unit = self.unit_input.currentText().strip()
        unit_price_text = self.unit_price_input.text().strip()
        try:
            unit_price = float(unit_price_text)
        except ValueError:
            QMessageBox.warning(
                self, "خطا", "لطفاً برای قیمت واحد یک عدد معتبر وارد کنید."
            )
            return

        if self.product_id:
            success, msg = self.db_manager.update_product(
                self.product_id,
                name,
                description,
                unit,
                unit_price,
                stock_quantity,
                account_id,
            )
        else:
            success, msg = self.db_manager.add_product(
                name, description, unit, unit_price, stock_quantity, account_id
            )

        if success:
            signal_bus.product_saved.emit()
            super().accept()
        else:
            QMessageBox.critical(self, "خطا", msg)
