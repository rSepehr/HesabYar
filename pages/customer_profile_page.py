# file: pages/customer_profile_page.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QFormLayout,
    QStackedWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor
from functools import partial

from pages.invoice_details_page import InvoiceDetailsPage

from utils import resource_path


class CustomerProfilePage(QWidget):
    back_to_list_requested = Signal()

    def __init__(self, customer_id, db_manager, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.db_manager = db_manager

        self.stack = QStackedWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)

        self.profile_main_page = QWidget()
        self.setup_profile_main_ui()
        self.stack.addWidget(self.profile_main_page)

        self.load_data()

    def setup_profile_main_ui(self):
        """UI صفحه اصلی پروفایل را راه‌اندازی می‌کند."""
        layout = QVBoxLayout(self.profile_main_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("پروفایل مشتری", objectName="dialogTitleLabel")
        back_btn = QPushButton(
            " بازگشت به لیست مشتریان",
            icon=QIcon(resource_path("assets/icons/arrow-right.svg")),
        )
        back_btn.clicked.connect(self.back_to_list_requested.emit)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        customer_frame = QFrame(objectName="formDialog")
        customer_info_layout = QVBoxLayout(customer_frame)
        customer_info_layout.addWidget(self.title_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        self.name_label = QLabel()
        self.national_id_label = QLabel()
        self.economic_code_label = QLabel()
        self.phone_label = QLabel()
        self.email_label = QLabel()
        self.address_label = QLabel()
        self.postal_code_label = QLabel()
        form_layout.addRow("<b>نام شخص/شرکت:</b>", self.name_label)
        form_layout.addRow("<b>کد/شناسه ملی:</b>", self.national_id_label)
        form_layout.addRow("<b>کد اقتصادی:</b>", self.economic_code_label)
        form_layout.addRow("<b>شماره تلفن:</b>", self.phone_label)
        form_layout.addRow("<b>ایمیل:</b>", self.email_label)
        form_layout.addRow("<b>آدرس:</b>", self.address_label)
        form_layout.addRow("<b>کد پستی:</b>", self.postal_code_label)
        customer_info_layout.addLayout(form_layout)
        layout.addWidget(customer_frame)

        layout.addWidget(QLabel("لیست فاکتورهای این مشتری:"))
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(5)
        self.invoices_table.setHorizontalHeaderLabels(
            ["شماره فاکتور", "تاریخ صدور", "مبلغ کل", "وضعیت", "عملیات"]
        )
        self.invoices_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.invoices_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.invoices_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.invoices_table, 1)

    def load_data(self):
        """داده‌های مشتری و فاکتورهای او را بارگذاری و نمایش می‌دهد."""
        customer_data = self.db_manager.get_customer_by_id(self.customer_id)
        if not customer_data:
            return

        self.title_label.setText(f"پروفایل مشتری: {customer_data['name']}")
        self.name_label.setText(customer_data["name"])
        self.national_id_label.setText(customer_data["national_id"] or "ثبت نشده")
        self.economic_code_label.setText(customer_data["economic_code"] or "ثبت نشده")
        self.phone_label.setText(customer_data["phone"] or "ثبت نشده")
        self.email_label.setText(customer_data["email"] or "ثبت نشده")
        self.address_label.setText(customer_data["address"] or "ثبت نشده")
        self.postal_code_label.setText(customer_data["postal_code"] or "ثبت نشده")

        invoices = self.db_manager.get_invoices_for_customer(self.customer_id)
        self.invoices_table.setRowCount(len(invoices))

        for row, invoice in enumerate(invoices):
            invoice_id = invoice["id"]
            self.invoices_table.setItem(
                row, 0, QTableWidgetItem(f"INV-{invoice_id:04d}")
            )
            self.invoices_table.setItem(row, 1, QTableWidgetItem(invoice["issue_date"]))
            self.invoices_table.setItem(
                row, 2, QTableWidgetItem(f"{invoice['total_amount']:,.0f} ریال")
            )

            status_text, status_color = self.get_status_display(invoice)
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_color)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 3, status_item)

            details_btn = QPushButton("مشاهده جزئیات")
            details_btn.clicked.connect(partial(self.show_invoice_details, invoice_id))
            self.invoices_table.setCellWidget(row, 4, details_btn)

    def show_invoice_details(self, invoice_id):
        """صفحه جزئیات فاکتور را ساخته و نمایش می‌دهد."""
        self.invoice_page = InvoiceDetailsPage(invoice_id, self.db_manager)
        self.invoice_page.back_requested.connect(self.show_profile_page)

        if self.stack.count() > 1:
            self.stack.removeWidget(self.stack.widget(1))

        self.stack.addWidget(self.invoice_page)
        self.stack.setCurrentWidget(self.invoice_page)

    def show_profile_page(self):
        """به صفحه اصلی پروفایل مشتری بازمی‌گردد."""
        self.stack.setCurrentWidget(self.profile_main_page)
        if hasattr(self, "invoice_page"):
            self.stack.removeWidget(self.invoice_page)
            self.invoice_page.deleteLater()
            del self.invoice_page

    def get_status_display(self, invoice):
        """متن و رنگ مناسب برای وضعیت فاکتور را برمی‌گرداند."""
        status = invoice["status"]
        if status == "Paid":
            return "پرداخت شده", QColor("#2ecc71")
        elif status == "Partially Paid":
            remaining = invoice["total_amount"] - (invoice["amount_paid"] or 0)
            return f"کسری: {remaining:,.0f} ریال", QColor("#f39c12")
        else:
            return "پرداخت نشده", QColor("#e74c3c")
