# file: pages/suppliers_page.py
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

from dialogs.supplier_dialog import SupplierDialog
from dialogs.custom_message_box import CustomMessageBox
from signal_bus import signal_bus
from utils import resource_path


class SuppliersPage(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="جستجو بر اساس نام...")
        add_btn = QPushButton(" افزودن تامین‌کننده", objectName="primaryButton")
        add_btn.setIcon(QIcon(resource_path("assets/icons/user-plus.svg")))
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(add_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "نام تامین‌کننده", "تلفن", "آدرس", "کد ملی/شناسه", "عملیات"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setColumnHidden(0, True)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.table)

        add_btn.clicked.connect(self.add_new_supplier)
        signal_bus.supplier_saved.connect(self.refresh_data)

        self.load_suppliers()

    def load_suppliers(self):
        suppliers = self.db_manager.get_all_suppliers()
        self.table.setRowCount(len(suppliers))
        for row, supplier in enumerate(suppliers):
            self.table.setItem(row, 0, QTableWidgetItem(str(supplier["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(supplier["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(supplier["phone"]))
            self.table.setItem(row, 3, QTableWidgetItem(supplier["address"]))
            self.table.setItem(row, 4, QTableWidgetItem(supplier["national_id"]))
            self.add_action_buttons(row, supplier["id"])

    def add_action_buttons(self, row, supplier_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        edit_btn = QPushButton(icon=QIcon(resource_path("assets/icons/edit-2.svg")), toolTip="ویرایش")
        delete_btn = QPushButton(icon=QIcon(resource_path("assets/icons/trash-2.svg")), toolTip="حذف")

        edit_btn.clicked.connect(lambda: self.edit_supplier(supplier_id))
        delete_btn.clicked.connect(lambda: self.delete_supplier(supplier_id))

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        self.table.setCellWidget(row, 5, widget)

    def add_new_supplier(self):
        dialog = SupplierDialog(self.db_manager, parent=self)
        dialog.exec()

    def edit_supplier(self, supplier_id):
        dialog = SupplierDialog(self.db_manager, supplier_id=supplier_id, parent=self)
        dialog.exec()

    def delete_supplier(self, supplier_id):
        confirm = CustomMessageBox(
            "تایید حذف", "آیا از حذف این تامین‌کننده مطمئن هستید؟", self
        )
        if confirm.exec() == QDialog.DialogCode.Accepted:
            success, msg = self.db_manager.delete_supplier(supplier_id)
            if success:
                QMessageBox.information(self, "موفق", msg)
                self.refresh_data()
            else:
                QMessageBox.critical(self, "خطا", msg)

    def refresh_data(self):
        self.search_input.clear()
        self.load_suppliers()
