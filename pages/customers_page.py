# file: pages/customers_page.py
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
    QStackedWidget,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from dialogs.customer_dialog import CustomerDialog
from dialogs.custom_message_box import CustomMessageBox
from signal_bus import signal_bus
from pages.customer_profile_page import CustomerProfilePage
from utils import resource_path


class CustomersPage(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        self.stack = QStackedWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)

        self.customer_list_page = QWidget()
        self.setup_customer_list_ui()
        self.stack.addWidget(self.customer_list_page)

        signal_bus.customer_saved.connect(self.refresh_data)
        self.table.doubleClicked.connect(self.handle_double_click)

        self.load_customers()

    def setup_customer_list_ui(self):
        """UI صفحه اصلی که لیست مشتریان را نمایش می‌دهد، راه‌اندازی می‌کند."""
        layout = QVBoxLayout(self.customer_list_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="جستجو بر اساس نام یا کد ملی...")
        self.search_input.textChanged.connect(self.search_customers)

        self.add_btn = QPushButton(" افزودن مشتری جدید", objectName="primaryButton")
        self.add_btn.setIcon(QIcon(resource_path("assets/icons/user-plus.svg")))
        self.add_btn.clicked.connect(self.open_add_dialog)

        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.add_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "نام", "کد/شناسه ملی", "تلفن", "ایمیل", "آدرس", "عملیات"]
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

    def load_customers(self, search_term=None):
        """داده‌های مشتریان را از دیتابیس بارگذاری و در جدول نمایش می‌دهد."""
        customers = (
            self.db_manager.search_customers(search_term)
            if search_term
            else self.db_manager.get_all_customers()
        )
        self.table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            self.table.setItem(row, 0, QTableWidgetItem(str(customer["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(customer["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(customer["national_id"]))
            self.table.setItem(row, 3, QTableWidgetItem(customer["phone"]))
            self.table.setItem(row, 4, QTableWidgetItem(customer["email"]))
            self.table.setItem(row, 5, QTableWidgetItem(customer["address"]))
            self.add_action_buttons(row, customer["id"])

        self.table.setColumnHidden(0, True)

    def add_action_buttons(self, row, customer_id):
        """دکمه‌های عملیات (پروفایل، ویرایش، حذف) را به جدول اضافه می‌کند."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        profile_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/eye.svg")),
            toolTip="مشاهده پروفایل",
            parent=self,
        )
        profile_btn.setProperty("class", "actionButton")
        profile_btn.clicked.connect(lambda: self.show_customer_profile(customer_id))

        edit_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/edit-2.svg")),
            toolTip="ویرایش",
            parent=self,
        )
        edit_btn.setProperty("class", "actionButton")
        edit_btn.clicked.connect(lambda: self.open_edit_dialog(customer_id))

        delete_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/trash-2.svg")),
            toolTip="حذف",
            parent=self,
        )
        delete_btn.setProperty("class", "actionButton")
        delete_btn.clicked.connect(lambda: self.delete_customer(customer_id))

        layout.addWidget(profile_btn)
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        self.table.setCellWidget(row, 6, widget)

    def handle_double_click(self, index):
        """با دو بار کلیک روی یک ردیف، پروفایل مشتری را نمایش می‌دهد."""
        row = index.row()
        customer_id = int(self.table.item(row, 0).text())
        self.show_customer_profile(customer_id)

    def show_customer_profile(self, customer_id):
        """صفحه پروفایل مشتری را ساخته و نمایش می‌دهد."""
        self.profile_page_widget = CustomerProfilePage(customer_id, self.db_manager)
        self.profile_page_widget.back_to_list_requested.connect(self.show_customer_list)

        if self.stack.count() > 1:
            self.stack.removeWidget(self.stack.widget(1))

        self.stack.addWidget(self.profile_page_widget)
        self.stack.setCurrentWidget(self.profile_page_widget)

    def show_customer_list(self):
        """به صفحه لیست مشتریان بازمی‌گردد."""
        self.stack.setCurrentWidget(self.customer_list_page)
        if hasattr(self, "profile_page_widget"):
            self.stack.removeWidget(self.profile_page_widget)
            self.profile_page_widget.deleteLater()
            del self.profile_page_widget

    def open_add_dialog(self):
        dialog = CustomerDialog(self.db_manager, parent=self)
        dialog.exec()

    def open_edit_dialog(self, customer_id):
        dialog = CustomerDialog(self.db_manager, customer_id=customer_id, parent=self)
        dialog.exec()

    def delete_customer(self, customer_id):
        confirm = CustomMessageBox(
            "تایید حذف",
            "آیا از حذف این مشتری مطمئن هستید؟\nبا حذف مشتری، تمام فاکتورهای او نیز حذف خواهند شد.",
            self,
        )
        if confirm.exec() == QDialog.DialogCode.Accepted:
            success, msg = self.db_manager.delete_customer(customer_id)
            if success:
                QMessageBox.information(self, "موفق", msg)
                self.refresh_data()
            else:
                QMessageBox.critical(self, "خطا", msg)

    def search_customers(self):
        self.load_customers(self.search_input.text())

    def refresh_data(self):
        self.show_customer_list()
        self.search_input.clear()
        self.load_customers()
