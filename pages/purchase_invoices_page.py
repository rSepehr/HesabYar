# file: pages/purchase_invoices_page.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QStackedWidget,
)
from PySide6.QtGui import QIcon
from functools import partial

from dialogs.purchase_invoice_dialog import PurchaseInvoiceDialog
from dialogs.custom_message_box import CustomMessageBox
from signal_bus import signal_bus
from pages.purchase_invoice_details_page import (
    PurchaseInvoiceDetailsPage,
)
from utils import resource_path


class PurchaseInvoicesPage(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget(self)
        main_layout.addWidget(self.stack)

        self.list_page = QWidget()
        list_layout = QVBoxLayout(self.list_page)

        top_layout = QHBoxLayout()
        add_btn = QPushButton(" ثبت فاکتور خرید جدید", objectName="primaryButton")
        add_btn.setIcon(QIcon(resource_path("assets/icons/file-plus.svg")))
        top_layout.addStretch()
        top_layout.addWidget(add_btn)
        list_layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "شماره فاکتور", "تامین‌کننده", "تاریخ", "مبلغ کل", "عملیات"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setColumnHidden(0, True)
        list_layout.addWidget(self.table)

        self.stack.addWidget(self.list_page)

        add_btn.clicked.connect(self.add_new_purchase_invoice)
        signal_bus.purchase_invoice_saved.connect(self.load_data)
        self.table.doubleClicked.connect(
            lambda index: self.show_details_page_by_index(index)
        )

        self.load_data()

    def load_data(self):
        self.stack.setCurrentWidget(self.list_page)
        invoices = self.db_manager.get_all_purchase_invoices()
        self.table.setRowCount(len(invoices))
        for row, inv in enumerate(invoices):
            self.table.setItem(row, 0, QTableWidgetItem(str(inv["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(f"PI-{inv['id']:04d}"))
            self.table.setItem(
                row, 2, QTableWidgetItem(inv["supplier_name"] or "حذف شده")
            )
            self.table.setItem(row, 3, QTableWidgetItem(inv["issue_date"]))
            self.table.setItem(
                row, 4, QTableWidgetItem(f"{inv['total_amount']:,.0f} ریال")
            )
            self.add_action_buttons(row, inv["id"])

    def add_action_buttons(self, row, invoice_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        details_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/eye.svg")), toolTip="مشاهده جزئیات"
        )
        delete_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/trash-2.svg")), toolTip="حذف"
        )

        details_btn.clicked.connect(partial(self.show_details_page, invoice_id))
        delete_btn.clicked.connect(partial(self.delete_invoice, invoice_id))

        layout.addWidget(details_btn)
        layout.addWidget(delete_btn)
        self.table.setCellWidget(row, 5, widget)

    def show_details_page(self, invoice_id):
        details_page = PurchaseInvoiceDetailsPage(invoice_id, self.db_manager)
        details_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.list_page)
        )
        self.stack.addWidget(details_page)
        self.stack.setCurrentWidget(details_page)

    def show_details_page_by_index(self, index):
        row = index.row()
        invoice_id = int(self.table.item(row, 0).text())
        self.show_details_page(invoice_id)

    def add_new_purchase_invoice(self):
        dialog = PurchaseInvoiceDialog(self.db_manager, parent=self)
        dialog.exec()

    def delete_invoice(self, invoice_id):
        confirm = CustomMessageBox(
            "تایید حذف", "آیا از حذف این فاکتور خرید مطمئن هستید؟", self
        )
        if confirm.exec() == QDialog.DialogCode.Accepted:
            success, msg = self.db_manager.delete_purchase_invoice(invoice_id)
            if success:
                QMessageBox.information(self, "موفقیت", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "خطا", msg)
