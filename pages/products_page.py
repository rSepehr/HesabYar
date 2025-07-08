# file: pages/products_page.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from dialogs.product_dialog import ProductDialog
from dialogs.custom_message_box import CustomMessageBox
from signal_bus import signal_bus
from utils import resource_path


class ProductsPage(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        signal_bus.product_saved.connect(self.refresh_data)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="جستجو بر اساس نام یا توضیحات...")
        self.search_input.textChanged.connect(self.search_products)
        self.add_btn = QPushButton(" افزودن کالا/خدمات", objectName="primaryButton")
        self.add_btn.setIcon(QIcon(resource_path("assets/icons/package.svg")))
        self.add_btn.clicked.connect(self.open_add_dialog)
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.add_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "نام کالا/خدمات", "توضیحات", "واحد", "قیمت واحد", "موجودی", "عملیات"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.table)

        self.load_products()

    def load_products(self, search_term=None):
        products = (
            self.db_manager.search_products(search_term)
            if search_term
            else self.db_manager.get_all_products()
        )
        self.table.setRowCount(len(products))
        for row, product in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(str(product["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(product["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(product["description"]))
            self.table.setItem(row, 3, QTableWidgetItem(product["unit"]))
            self.table.setItem(
                row, 4, QTableWidgetItem(f"{product['unit_price']:,.0f} ریال")
            )
            stock_qty = (
                product["stock_quantity"] if "stock_quantity" in product.keys() else 0
            )
            self.table.setItem(row, 5, QTableWidgetItem(str(stock_qty)))

            self.add_action_buttons(row, product["id"])

        self.table.setColumnHidden(0, True)

    def add_action_buttons(self, row, product_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/edit-2.svg")),
            toolTip="ویرایش",
            parent=self,
        )
        edit_btn.setProperty("class", "actionButton")
        edit_btn.clicked.connect(lambda: self.open_edit_dialog(product_id))
        delete_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/trash-2.svg")),
            toolTip="حذف",
            parent=self,
        )
        delete_btn.setProperty("class", "actionButton")
        delete_btn.clicked.connect(lambda: self.delete_product(product_id))
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        self.table.setCellWidget(row, 6, widget)

    def open_add_dialog(self):
        dialog = ProductDialog(self.db_manager, parent=self)
        dialog.exec()

    def open_edit_dialog(self, product_id):
        dialog = ProductDialog(self.db_manager, product_id=product_id, parent=self)
        dialog.exec()

    def delete_product(self, product_id):
        confirm = CustomMessageBox(
            "تایید حذف", "آیا از حذف این کالا مطمئن هستید؟", self
        )
        if confirm.exec() == QDialog.DialogCode.Accepted:
            success, msg = self.db_manager.delete_product(product_id)
            if success:
                QMessageBox.information(self, "موفق", msg)
                self.refresh_data()
            else:
                QMessageBox.critical(self, "خطا", msg)

    def search_products(self):
        self.load_products(self.search_input.text())

    def refresh_data(self):
        self.search_input.clear()
        self.load_products()
