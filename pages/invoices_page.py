# file: pages/invoices_page.py
import os
import sys
import subprocess
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
    QLabel,
    QComboBox,
    QStackedWidget,
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QColor
from functools import partial

from dialogs.invoice_dialog import InvoiceDialog
from dialogs.custom_message_box import CustomMessageBox
from dialogs.pdf_success_dialog import PdfSuccessDialog
from dialogs.payment_dialog import PaymentDialog
from signal_bus import signal_bus
from pdf_generator import generate_invoice_pdf
from pages.invoice_details_page import InvoiceDetailsPage
from utils import resource_path


class InvoicesPage(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        self.stack = QStackedWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)

        self.invoice_list_page = QWidget()
        self.setup_invoice_list_ui()
        self.stack.addWidget(self.invoice_list_page)

        signal_bus.invoice_saved.connect(self.refresh_data)
        self.table.doubleClicked.connect(self.handle_double_click)

    def setup_invoice_list_ui(self):
        """UI صفحه اصلی که لیست فاکتورها را نمایش می‌دهد، راه‌اندازی می‌کند."""
        layout = QVBoxLayout(self.invoice_list_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit(
            placeholderText="جستجو بر اساس نام مشتری یا شماره فاکتور..."
        )
        self.search_input.textChanged.connect(self.search_invoices)
        top_layout.addWidget(self.search_input)

        top_layout.addStretch()
        top_layout.addWidget(QLabel("سایز چاپ:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "A5"])
        top_layout.addWidget(self.page_size_combo)

        self.add_invoice_btn = QPushButton(
            " صدور فاکتور جدید", objectName="primaryButton"
        )
        self.add_invoice_btn.setIcon(QIcon(resource_path("assets/icons/file-plus.svg")))
        self.add_invoice_btn.clicked.connect(self.open_add_invoice_dialog)
        top_layout.addWidget(self.add_invoice_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "شماره", "مشتری", "تاریخ صدور", "مبلغ کل", "وضعیت", "عملیات"]
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
        self.load_invoices()

    def search_invoices(self):
        """فاکتورها را بر اساس متن جستجو فیلتر می‌کند."""
        self.load_invoices(self.search_input.text())

    def load_invoices(self, search_term=None):
        """فاکتورها را از دیتابیس بارگذاری و در جدول نمایش می‌دهد."""
        try:
            self.table.setRowCount(0)
            invoices = (
                self.db_manager.search_invoices(search_term)
                if search_term
                else self.db_manager.get_all_invoices()
            )

            self.table.setRowCount(len(invoices))
            for row, invoice in enumerate(invoices):
                invoice_id = invoice["id"]
                self.table.setItem(row, 0, QTableWidgetItem(str(invoice_id)))
                self.table.setItem(row, 1, QTableWidgetItem(f"INV-{invoice_id:04d}"))
                self.table.setItem(row, 2, QTableWidgetItem(invoice["customer_name"]))
                self.table.setItem(row, 3, QTableWidgetItem(invoice["issue_date"]))
                self.table.setItem(
                    row, 4, QTableWidgetItem(f"{invoice['total_amount']:,.0f} ریال")
                )

                status_text, status_color = self.get_status_display(invoice)
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(status_color)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 5, status_item)

                self.add_action_buttons(
                    row,
                    invoice_id,
                    invoice["status"],
                    invoice["total_amount"],
                    invoice["amount_paid"],
                )

            self.table.setColumnHidden(0, True)
        except Exception as e:
            QMessageBox.critical(self, "خطا در بارگذاری فاکتورها", f"خطایی رخ داد: {e}")

    def add_action_buttons(self, row, invoice_id, status, total_amount, amount_paid):
        """دکمه‌های عملیات را به جدول اضافه می‌کند، شامل دکمه ثبت پرداخت."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        details_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/eye.svg")), toolTip="مشاهده جزئیات"
        )
        details_btn.setProperty("class", "actionButton")
        details_btn.clicked.connect(partial(self.show_invoice_details, invoice_id))
        layout.addWidget(details_btn)

        if status in ["پرداخت نشده", "کسری"]:
            remaining_balance = total_amount - (amount_paid or 0)
            payment_btn = QPushButton(
                icon=QIcon(resource_path("assets/icons/credit-card.svg")),
                toolTip="ثبت پرداخت جدید",
            )
            payment_btn.setProperty("class", "actionButton")
            payment_btn.clicked.connect(
                lambda: self.open_payment_dialog(invoice_id, remaining_balance)
            )
            layout.addWidget(payment_btn)

        print_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/printer.svg")),
            toolTip="چاپ/نمایش PDF",
        )
        print_btn.setProperty("class", "actionButton")
        print_btn.clicked.connect(lambda: self.print_invoice(invoice_id))
        layout.addWidget(print_btn)

        delete_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/trash-2.svg")), toolTip="حذف فاکتور"
        )
        delete_btn.setProperty("class", "actionButton")
        delete_btn.clicked.connect(lambda: self.delete_invoice(invoice_id))
        layout.addWidget(delete_btn)

        self.table.setCellWidget(row, 6, widget)

    def handle_double_click(self, index):
        """با دو بار کلیک روی یک ردیف، جزئیات فاکتور را نمایش می‌دهد."""
        row = index.row()
        invoice_id = int(self.table.item(row, 0).text())
        self.show_invoice_details(invoice_id)

    def show_invoice_details(self, invoice_id):
        """صفحه جزئیات فاکتور را ساخته و نمایش می‌دهد."""
        self.details_page = InvoiceDetailsPage(invoice_id, self.db_manager)
        self.details_page.back_requested.connect(self.show_invoice_list)

        if self.stack.count() > 1:
            self.stack.removeWidget(self.stack.widget(1))

        self.stack.addWidget(self.details_page)
        self.stack.setCurrentWidget(self.details_page)

    def show_invoice_list(self):
        """به صفحه لیست فاکتورها بازمی‌گردد."""
        self.stack.setCurrentWidget(self.invoice_list_page)
        if hasattr(self, "details_page"):
            self.stack.removeWidget(self.details_page)
            self.details_page.deleteLater()
            del self.details_page

    def get_status_display(self, invoice):
        """متن و رنگ مناسب برای وضعیت فاکتور را برمی‌گرداند."""
        status = invoice["status"]

        if status == "پرداخت شده":
            return "پرداخت شده", QColor("#2ecc71")
        elif status == "کسری":
            # محاسبه مبلغ باقی‌مانده مثل قبل
            remaining = invoice["total_amount"] - (invoice["amount_paid"] or 0)
            return f"کسری: {remaining:,.0f} ریال", QColor("#f39c12")
        else:  # این حالت برای "پرداخت نشده" است
            return "پرداخت نشده", QColor("#e74c3c")

    def print_invoice(self, invoice_id):
        page_size = self.page_size_combo.currentText()

        invoice_details_row = self.db_manager.get_invoice_details(invoice_id)
        items_data_rows = self.db_manager.get_invoice_items(invoice_id)

        if not invoice_details_row:
            QMessageBox.critical(self, "خطا", "اطلاعات فاکتور برای چاپ یافت نشد.")
            return

        invoice_details = dict(invoice_details_row)
        items_data = [dict(item) for item in items_data_rows]

        settings = QSettings("MySoft", "HesabYar")
        company_info = {
            "name": settings.value("company/name", ""),
            "national_id": settings.value("company/national_id", ""),
            "economic_code": settings.value("company/economic_code", ""),
            "phone": settings.value("company/phone", ""),
            "landline": settings.value("company/landline", ""),
            "postal_code": settings.value("company/postal_code", ""),
            "address": settings.value("company/address", ""),
            "logo_path": settings.value("company/logo_path", None),
        }

        if invoice_details and items_data is not None:
            file_path, success = generate_invoice_pdf(
                invoice_details, items_data, company_info, page_size_str=page_size
            )
            if success:
                self.show_success_dialog(file_path)
            else:
                QMessageBox.critical(self, "خطا", f"خطا در ساخت فایل PDF:\n{file_path}")
        else:
            QMessageBox.critical(
                self, "خطا", "اطلاعات فاکتور یا اقلام آن برای چاپ یافت نشد."
            )

    def delete_invoice(self, invoice_id):
        confirm = CustomMessageBox(
            "تایید حذف", "آیا از حذف این فاکتور مطمئن هستید؟", self
        )
        if confirm.exec() == QDialog.Accepted:
            success, msg = self.db_manager.delete_invoice(invoice_id)
            if success:
                QMessageBox.information(self, "موفق", msg)
                signal_bus.invoice_saved.emit()
            else:
                QMessageBox.critical(self, "خطا", msg)

    def open_add_invoice_dialog(self):
        dialog = InvoiceDialog(self.db_manager, parent=self)
        dialog.exec()

    def open_payment_dialog(self, invoice_id, remaining_balance):
        """دیالوگ ثبت پرداخت را برای یک فاکتور مشخص باز می‌کند."""
        dialog = PaymentDialog(
            self.db_manager, invoice_id, remaining_balance, parent=self
        )
        dialog.exec()

    def show_success_dialog(self, file_path):
        folder_path = os.path.dirname(file_path)
        dialog = PdfSuccessDialog(f"فایل PDF در مسیر زیر ساخته شد:\n{file_path}", self)
        result = dialog.exec()
        try:
            if result == dialog.OpenFile:
                if sys.platform == "win32":
                    os.startfile(file_path)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.run([opener, file_path])
            elif result == dialog.OpenFolder:
                if sys.platform == "win32":
                    os.startfile(folder_path)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.run([opener, folder_path])
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن: {e}")

    def refresh_data(self):
        """داده‌ها را رفرش کرده و به صفحه لیست بازمی‌گردد."""
        self.show_invoice_list()
        self.search_input.clear()
        self.load_invoices()
