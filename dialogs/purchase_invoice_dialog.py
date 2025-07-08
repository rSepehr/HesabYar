# file: dialogs/purchase_invoice_dialog.py
import jdatetime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QTextEdit,
    QMessageBox,
    QWidget,
    QHeaderView,
    QLineEdit,
)
from PySide6.QtCore import Qt
from signal_bus import signal_bus


class PurchaseInvoiceDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.products = self.db_manager.get_all_products()

        self.setWindowTitle("ثبت فاکتور خرید جدید")
        self.setObjectName("formDialog")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.supplier_combo = QComboBox()
        self.issue_date_edit = QLineEdit(jdatetime.date.today().strftime("%Y/%m/%d"))

        form_layout.addRow("انتخاب تامین‌کننده:", self.supplier_combo)
        form_layout.addRow("تاریخ ثبت:", self.issue_date_edit)
        layout.addLayout(form_layout)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(
            ["نام کالا", "تعداد خرید", "قیمت خرید (واحد)", "جمع کل"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.items_table.cellChanged.connect(self.update_totals)
        layout.addWidget(self.items_table)

        buttons_layout = QHBoxLayout()
        add_item_btn = QPushButton("افزودن کالا")
        remove_item_btn = QPushButton("حذف کالا")
        buttons_layout.addStretch()
        buttons_layout.addWidget(add_item_btn)
        buttons_layout.addWidget(remove_item_btn)
        layout.addLayout(buttons_layout)

        self.notes_edit = QTextEdit(placeholderText="توضیحات (اختیاری)...")
        self.total_amount_label = QLabel("جمع کل فاکتور: ۰ ریال")
        self.total_amount_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        layout.addWidget(self.notes_edit)
        layout.addWidget(self.total_amount_label, 0, Qt.AlignmentFlag.AlignLeft)

        save_button = QPushButton("ذخیره فاکتور خرید", objectName="primaryButton")
        layout.addWidget(save_button)

        add_item_btn.clicked.connect(self.add_item_row)
        remove_item_btn.clicked.connect(self.remove_item_row)
        save_button.clicked.connect(self.save_invoice)

        self.load_initial_data()

    def load_initial_data(self):
        suppliers = self.db_manager.get_all_suppliers()
        for supplier in suppliers:
            self.supplier_combo.addItem(supplier["name"], userData=supplier["id"])

    def add_item_row(self):
        row_position = self.items_table.rowCount()
        self.items_table.insertRow(row_position)

        product_combo = QComboBox()
        for p in self.products:
            product_combo.addItem(p["name"], userData=p["id"])

        self.items_table.setCellWidget(row_position, 0, product_combo)
        self.items_table.setItem(row_position, 1, QTableWidgetItem("1"))
        self.items_table.setItem(row_position, 2, QTableWidgetItem("0"))
        self.items_table.setItem(row_position, 3, QTableWidgetItem("0"))

    def remove_item_row(self):
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_table.removeRow(current_row)
            self.update_totals()

    def update_totals(self, row=None, column=None):
        grand_total = 0
        for r in range(self.items_table.rowCount()):
            try:
                quantity_item = self.items_table.item(r, 1)
                price_item = self.items_table.item(r, 2)
                if (
                    quantity_item
                    and price_item
                    and quantity_item.text()
                    and price_item.text()
                ):
                    quantity = float(quantity_item.text())
                    price = float(price_item.text())
                    total = quantity * price
                    self.items_table.blockSignals(True)
                    self.items_table.setItem(r, 3, QTableWidgetItem(f"{total:,.0f}"))
                    self.items_table.blockSignals(False)
                    grand_total += total
            except (ValueError, TypeError, AttributeError):
                continue
        self.total_amount_label.setText(f"جمع کل فاکتور: {grand_total:,.0f} ریال")

    def save_invoice(self):
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            QMessageBox.warning(self, "خطا", "لطفاً یک تامین‌کننده انتخاب کنید.")
            return

        items_to_save = []
        products_to_update = []
        grand_total = 0

        for row in range(self.items_table.rowCount()):
            product_combo = self.items_table.cellWidget(row, 0)
            product_id = product_combo.currentData()
            product_name = product_combo.currentText()

            try:
                quantity = float(self.items_table.item(row, 1).text())
                purchase_price = float(self.items_table.item(row, 2).text())
                if quantity <= 0 or purchase_price < 0:
                    QMessageBox.warning(
                        self,
                        "خطا",
                        f"مقادیر تعداد و قیمت در ردیف {row+1} باید معتبر باشند.",
                    )
                    return

                items_to_save.append(
                    {
                        "product_name": product_name,
                        "quantity": quantity,
                        "purchase_price": purchase_price,
                    }
                )
                products_to_update.append(
                    {"id": product_id, "quantity": quantity, "price": purchase_price}
                )
                grand_total += quantity * purchase_price
            except (ValueError, TypeError, AttributeError):
                QMessageBox.warning(self, "خطا", f"مقادیر در ردیف {row+1} نامعتبر است.")
                return

        if not items_to_save:
            QMessageBox.warning(
                self, "خطا", "فاکتور خرید باید حداقل شامل یک کالا باشد."
            )
            return

        invoice_data = {
            "supplier_id": supplier_id,
            "issue_date": self.issue_date_edit.text(),
            "total_amount": grand_total,
            "notes": self.notes_edit.toPlainText(),
        }

        success, msg, _ = self.db_manager.save_purchase_invoice(
            invoice_data, items_to_save
        )

        if success:
            for product in products_to_update:
                self.db_manager.update_product_after_purchase(
                    product["id"], product["quantity"], product["price"]
                )

            QMessageBox.information(self, "موفقیت", msg)
            signal_bus.purchase_invoice_saved.emit()
            signal_bus.product_saved.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "خطا", msg)
