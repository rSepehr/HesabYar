# file: pages/dashboard_page.py
import jdatetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QFont, QIcon, QColor
from utils import resource_path


class DashboardPage(QWidget):
    add_invoice_requested = Signal()
    add_customer_requested = Signal()
    add_expense_requested = Signal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        self.welcome_text_label = QLabel()
        main_layout.addWidget(self.welcome_text_label, 0, Qt.AlignmentFlag.AlignRight)

        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        self.sales_kpi, self.sales_val = self._create_kpi_box(
            "فروش این ماه", resource_path("assets/icons/trending-up.svg"), "#27ae60"
        )
        self.expenses_kpi, self.expenses_val = self._create_kpi_box(
            "هزینه این ماه", resource_path("assets/icons/trending-down.svg"), "#c0392b"
        )
        self.profit_kpi, self.profit_val = self._create_kpi_box(
            "سود خالص ماه", resource_path("assets/icons/dollar-sign.svg"), "#2980b9"
        )
        kpi_layout.addWidget(self.sales_kpi)
        kpi_layout.addWidget(self.expenses_kpi)
        kpi_layout.addWidget(self.profit_kpi)
        main_layout.addLayout(kpi_layout)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        self.low_stock_frame = self._create_info_table_box(
            "هشدار موجودی کالا (۱۰ عدد یا کمتر)",
            resource_path("assets/icons/alert-triangle.svg"),
        )
        self.low_stock_table = self.low_stock_frame.findChild(QTableWidget)

        self.upcoming_cheques_frame = self._create_info_table_box(
            "چک‌های در انتظار وصول", resource_path("assets/icons/credit-card.svg")
        )
        self.upcoming_cheques_table = self.upcoming_cheques_frame.findChild(
            QTableWidget
        )

        self.quick_access_frame = self._create_quick_access_section()

        grid_layout.addWidget(self.low_stock_frame, 0, 0)
        grid_layout.addWidget(self.upcoming_cheques_frame, 0, 1)
        grid_layout.addWidget(self.quick_access_frame, 0, 2)
        grid_layout.setColumnStretch(0, 2)
        grid_layout.setColumnStretch(1, 2)
        grid_layout.setColumnStretch(2, 1)
        main_layout.addLayout(grid_layout, 1)

        self.company_info_frame = self._create_company_info_section()
        main_layout.addWidget(self.company_info_frame)

        self.refresh_dashboard()

    def _create_kpi_box(self, title, icon_path, color):
        frame = QFrame(objectName="kpiBox")
        layout = QVBoxLayout(frame)
        top_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(resource_path(icon_path)).pixmap(24, 24))
        title_label = QLabel(title, objectName="kpiTitleLabel")
        top_layout.addWidget(icon_label)
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        value_label = QLabel("۰", objectName="kpiValueLabel")
        value_label.setStyleSheet(f"color: {color};")
        layout.addLayout(top_layout)
        layout.addWidget(value_label)
        return frame, value_label

    def _create_info_table_box(self, title, icon_path):
        frame = QFrame(objectName="formDialog")
        layout = QVBoxLayout(frame)
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(resource_path(icon_path)).pixmap(20, 20))
        title_label = QLabel(title, objectName="dialogTitleLabel")
        title_layout.addStretch()
        title_layout.addWidget(title_label)
        title_layout.addWidget(icon_label)
        layout.addLayout(title_layout)
        table = QTableWidget()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(table)
        return frame

    def _create_quick_access_section(self):
        frame = QFrame(objectName="formDialog")
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title = QLabel("دسترسی سریع", objectName="dialogTitleLabel")
        layout.addWidget(title)
        add_invoice_btn = QPushButton(
            " صدور فاکتور جدید", icon=QIcon(resource_path("assets/icons/file-plus.svg"))
        )
        add_customer_btn = QPushButton(
            " افزودن مشتری جدید",
            icon=QIcon(resource_path("assets/icons/user-plus.svg")),
        )
        add_expense_btn = QPushButton(
            " ثبت هزینه جدید", icon=QIcon(resource_path("assets/icons/dollar-sign.svg"))
        )
        add_invoice_btn.clicked.connect(self.add_invoice_requested.emit)
        add_customer_btn.clicked.connect(self.add_customer_requested.emit)
        add_expense_btn.clicked.connect(self.add_expense_requested.emit)
        layout.addWidget(add_invoice_btn)
        layout.addWidget(add_customer_btn)
        layout.addWidget(add_expense_btn)
        layout.addStretch()
        return frame

    def _create_company_info_section(self):
        """ویجت نمایش اطلاعات شرکت را در پایین داشبورد ایجاد می‌کند."""
        frame = QFrame(objectName="formDialog")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)

        self.company_name_label = QLabel("<b>نام شرکت:</b> -")
        self.company_phone_label = QLabel("<b>تلفن:</b> -")
        self.company_address_label = QLabel("<b>آدرس:</b> -")

        layout.addWidget(self.company_name_label, 1)
        layout.addWidget(self.company_phone_label, 1)
        layout.addWidget(self.company_address_label, 2)
        return frame

    def refresh_dashboard(self):
        settings = QSettings("MySoft", "HesabYar")
        username = settings.value("last_username", "کاربر")
        self.welcome_text_label.setText(
            f"سلام <b>{username}</b>، به حساب‌یار خوش آمدید!"
        )

        try:
            today = jdatetime.date.today()
            start_of_month = today.replace(day=1).strftime("%Y/%m/%d")
            next_month = today.replace(day=28) + jdatetime.timedelta(days=4)
            end_of_month = (
                next_month - jdatetime.timedelta(days=next_month.day)
            ).strftime("%Y/%m/%d")

            summary = self.db_manager.get_financial_summary_by_date_range(
                start_of_month, end_of_month
            )
            self.sales_val.setText(f"{summary['total_revenue']:,.0f} ریال")
            self.expenses_val.setText(f"{summary['total_expenses']:,.0f} ریال")
            self.profit_val.setText(f"{summary['net_profit']:,.0f} ریال")
        except Exception as e:
            print(f"Error loading financial KPIs: {e}")

        try:
            self.low_stock_table.setColumnCount(2)
            self.low_stock_table.setHorizontalHeaderLabels(
                ["نام کالا", "تعداد باقی‌مانده"]
            )
            self.low_stock_table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch
            )
            self.low_stock_table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.ResizeToContents
            )
            low_stock_items = self.db_manager.get_low_stock_products(threshold=10)
            self.low_stock_table.setRowCount(len(low_stock_items))
            for row, item in enumerate(low_stock_items):
                self.low_stock_table.setItem(row, 0, QTableWidgetItem(item["name"]))
                self.low_stock_table.setItem(
                    row, 1, QTableWidgetItem(str(item["stock_quantity"]))
                )
        except Exception as e:
            print(f"Error loading low stock items: {e}")

        try:
            self.upcoming_cheques_table.setColumnCount(3)
            self.upcoming_cheques_table.setHorizontalHeaderLabels(
                ["شماره چک", "تاریخ سررسید", "مبلغ"]
            )
            self.upcoming_cheques_table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch
            )
            self.upcoming_cheques_table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.ResizeToContents
            )
            self.upcoming_cheques_table.horizontalHeader().setSectionResizeMode(
                2, QHeaderView.ResizeMode.ResizeToContents
            )
            upcoming_cheques = self.db_manager.get_upcoming_cheques(limit=5)
            self.upcoming_cheques_table.setRowCount(len(upcoming_cheques))
            for row, cheque in enumerate(upcoming_cheques):
                self.upcoming_cheques_table.setItem(
                    row, 0, QTableWidgetItem(cheque["cheque_number"])
                )
                self.upcoming_cheques_table.setItem(
                    row, 1, QTableWidgetItem(cheque["due_date"])
                )
                self.upcoming_cheques_table.setItem(
                    row, 2, QTableWidgetItem(f"{cheque['amount']:,.0f} ریال")
                )
        except Exception as e:
            print(f"Error loading upcoming cheques: {e}")

        try:
            company_name = settings.value("company/name", "ثبت نشده")
            company_phone = settings.value("company/phone", "ثبت نشده")
            company_address = settings.value("company/address", "ثبت نشده")
            self.company_name_label.setText(f"<b>نام شرکت:</b> {company_name}")
            self.company_phone_label.setText(f"<b>تلفن:</b> {company_phone}")
            self.company_address_label.setText(f"<b>آدرس:</b> {company_address}")
        except Exception as e:
            print(f"Error loading company info: {e}")
