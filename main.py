# file: main.py
import sys
import os
import jdatetime
import sqlite3
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QStackedWidget,
    QStatusBar,
)
from PySide6.QtCore import Qt, QSize, QSettings
from PySide6.QtGui import QIcon, QPixmap
from utils import get_app_data_path
from utils import resource_path


from database_setup import create_database
from db_updater import run_migrations

from db_manager import DatabaseManager
from auth_ui import AuthWindow
from pages.dashboard_page import DashboardPage
from pages.customers_page import CustomersPage
from pages.invoices_page import InvoicesPage
from pages.products_page import ProductsPage
from pages.reports_page import ReportsPage
from pages.settings_page import SettingsPage
from pages.expenses_page import ExpensesPage
from pages.profile_page import ProfilePage
from pages.cheques_page import ChequesPage
from pages.suppliers_page import SuppliersPage
from pages.purchase_invoices_page import PurchaseInvoicesPage
from dialogs.help_dialog import HelpDialog
from dialogs.about_dialog import AboutDialog

DB_NAME = get_app_data_path("accounting.db")


def initialize_database():
    """
    بررسی می‌کند که آیا دیتابیس به درستی ساخته شده یا نه.
    """
    db_conn = None
    try:
        db_conn = sqlite3.connect(DB_NAME)
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
        )
        table_exists = cursor.fetchone()

        if not table_exists:
            create_database(DB_NAME)
        else:
            run_migrations(DB_NAME)

    except sqlite3.Error as e:
        print(f"خطای جدی در اتصال یا آماده‌سازی دیتابیس: {e}")
    finally:
        if db_conn:
            db_conn.close()

    print("آماده‌سازی دیتابیس به پایان رسید.")


class AppMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("داشبورد اصلی - حساب‌یار")
        self.setMinimumSize(1100, 750)
        self.setWindowIcon(QIcon(resource_path("assets/images/icon.ico")))

        main_widget = QWidget()
        main_widget.setObjectName("mainWidget")

        main_widget.setStyleSheet("#mainWidget { padding: 0px; margin: 0px; }")

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        side_menu = QFrame(self, objectName="sideMenu")
        side_menu.setFixedWidth(220)

        side_menu_layout = QVBoxLayout(side_menu)
        side_menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        side_menu_layout.setContentsMargins(5, 10, 5, 10)
        side_menu_layout.setSpacing(5)

        logo_label = QLabel(self)
        pixmap = QPixmap(resource_path("assets/logo_menu.png"))
        logo_label.setPixmap(
            pixmap.scaled(
                70,
                70,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_menu_layout.addWidget(logo_label)

        today_date_str = jdatetime.date.today().strftime("%Y / %m / %d")
        date_label = QLabel(
            f"{today_date_str}",
            self,
            objectName="dateLabel",
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        side_menu_layout.addWidget(date_label)
        separator = QFrame(
            frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken
        )
        side_menu_layout.addWidget(separator)

        self.btn_dashboard = QPushButton(
            " داشبورد", icon=QIcon(resource_path("assets/icons/home.svg"))
        )
        self.btn_customers = QPushButton(
            " مشتریان", icon=QIcon(resource_path("assets/icons/users.svg"))
        )
        self.btn_suppliers = QPushButton(
            " تامین‌کنندگان", icon=QIcon(resource_path("assets/icons/truck.svg"))
        )
        self.btn_sales_invoices = QPushButton(
            " فاکتورهای فروش", icon=QIcon(resource_path("assets/icons/file-text.svg"))
        )
        self.btn_purchase_invoices = QPushButton(
            " فاکتورهای خرید",
            icon=QIcon(resource_path("assets/icons/shopping-cart.svg")),
        )
        self.btn_products = QPushButton(
            " کالاها و خدمات", icon=QIcon(resource_path("assets/icons/package.svg"))
        )
        self.btn_expenses = QPushButton(
            " هزینه‌ها", icon=QIcon(resource_path("assets/icons/dollar-sign.svg"))
        )
        self.btn_cheques = QPushButton(
            " چک‌ها", icon=QIcon(resource_path("assets/icons/credit-card.svg"))
        )
        self.btn_reports = QPushButton(
            " گزارش‌ها", icon=QIcon(resource_path("assets/icons/bar-chart-2.svg"))
        )
        self.btn_help = QPushButton(
            " راهنما", icon=QIcon(resource_path("assets/icons/help-circle.svg"))
        )
        self.btn_profile = QPushButton(
            " پروفایل کاربری", icon=QIcon(resource_path("assets/icons/user.svg"))
        )

        main_buttons = [
            self.btn_dashboard,
            self.btn_customers,
            self.btn_suppliers,
            self.btn_sales_invoices,
            self.btn_purchase_invoices,
            self.btn_products,
            self.btn_expenses,
            self.btn_cheques,
            self.btn_reports,
        ]
        for btn in main_buttons:
            side_menu_layout.addWidget(btn)

        side_menu_layout.addStretch()
        side_menu_layout.addWidget(self.btn_help)
        side_menu_layout.addWidget(self.btn_profile)
        self.btn_settings = QPushButton(
            " تنظیمات", icon=QIcon(resource_path("assets/icons/settings.svg"))
        )
        side_menu_layout.addWidget(self.btn_settings)

        all_buttons = main_buttons + [
            self.btn_help,
            self.btn_profile,
            self.btn_settings,
        ]
        for btn in all_buttons:
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.setAutoExclusive(True)

        self.main_content = QStackedWidget(self, objectName="mainContent")
        db_manager_for_pages = DatabaseManager()

        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        self.credit_label = QLabel(
            "ساخته شده توسط سپهر عبقری برای مردم عزیز ایران. | کلیک کنید"
        )
        self.credit_label.setToolTip("برای مشاهده اطلاعات بیشتر کلیک کنید")
        self.credit_label.setStyleSheet("padding-left: 10px; padding-right: 10px;")
        self.statusBar.addPermanentWidget(self.credit_label)
        self.credit_label.mousePressEvent = self.open_about_dialog
        self.dashboard_page = DashboardPage(db_manager_for_pages)
        self.customers_page = CustomersPage(db_manager_for_pages)
        self.invoices_page = InvoicesPage(db_manager_for_pages)
        self.products_page = ProductsPage(db_manager_for_pages)
        self.expenses_page = ExpensesPage(db_manager_for_pages)
        self.cheques_page = ChequesPage(db_manager_for_pages)
        self.suppliers_page = SuppliersPage(db_manager_for_pages)
        self.purchase_invoices_page = PurchaseInvoicesPage(db_manager_for_pages)
        self.reports_page = ReportsPage(db_manager_for_pages)
        self.profile_page = ProfilePage()
        self.settings_page = SettingsPage()

        self.main_content.addWidget(self.dashboard_page)  # ایندکس ۰
        self.main_content.addWidget(self.customers_page)  # ایندکس ۱
        self.main_content.addWidget(self.suppliers_page)  # ایندکس ۲
        self.main_content.addWidget(self.invoices_page)  # ایندکس ۳
        self.main_content.addWidget(self.purchase_invoices_page)  # ایندکس ۴
        self.main_content.addWidget(self.products_page)  # ایندکس ۵
        self.main_content.addWidget(self.expenses_page)  # ایندکس ۶
        self.main_content.addWidget(self.cheques_page)  # ایندکس ۷
        self.main_content.addWidget(self.reports_page)  # ایندکس ۸
        self.main_content.addWidget(self.profile_page)  # ایندکس ۹
        self.main_content.addWidget(self.settings_page)  # ایندکس ۱۰

        self.btn_dashboard.clicked.connect(lambda: self.main_content.setCurrentIndex(0))
        self.btn_customers.clicked.connect(lambda: self.main_content.setCurrentIndex(1))
        self.btn_suppliers.clicked.connect(lambda: self.main_content.setCurrentIndex(2))
        self.btn_sales_invoices.clicked.connect(
            lambda: self.main_content.setCurrentIndex(3)
        )
        self.btn_purchase_invoices.clicked.connect(
            lambda: self.main_content.setCurrentIndex(4)
        )
        self.btn_products.clicked.connect(lambda: self.main_content.setCurrentIndex(5))
        self.btn_expenses.clicked.connect(lambda: self.main_content.setCurrentIndex(6))
        self.btn_cheques.clicked.connect(lambda: self.main_content.setCurrentIndex(7))
        self.btn_reports.clicked.connect(lambda: self.main_content.setCurrentIndex(8))
        self.btn_profile.clicked.connect(lambda: self.main_content.setCurrentIndex(9))
        self.btn_settings.clicked.connect(lambda: self.main_content.setCurrentIndex(10))
        self.btn_help.clicked.connect(self.open_help_dialog)

        self.dashboard_page.add_invoice_requested.connect(
            self.handle_add_invoice_request
        )
        self.dashboard_page.add_customer_requested.connect(
            self.handle_add_customer_request
        )
        self.dashboard_page.add_expense_requested.connect(
            self.handle_add_expense_request
        )

        self.btn_dashboard.setChecked(True)
        self.main_content.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(side_menu)
        main_layout.addWidget(self.main_content)
        self.setCentralWidget(main_widget)
        self.on_tab_changed(0)

    def open_about_dialog(self, event=None):
        """دیالوگ «درباره ما» را باز می‌کند."""
        dialog = AboutDialog(self)
        dialog.exec()

    def handle_add_invoice_request(self):
        """به صفحه فاکتورها رفته و دیالوگ افزودن را باز می‌کند."""
        self.main_content.setCurrentWidget(self.invoices_page)
        self.invoices_page.open_add_invoice_dialog()

    def handle_add_customer_request(self):
        """به صفحه مشتریان رفته و دیالوگ افزودن را باز می‌کند."""
        self.main_content.setCurrentWidget(self.customers_page)
        self.customers_page.open_add_dialog()

    def handle_add_expense_request(self):
        """به صفحه هزینه‌ها رفته و دیالوگ افزودن را باز می‌کند."""
        self.main_content.setCurrentWidget(self.expenses_page)
        self.expenses_page.add_new_expense()

    def on_tab_changed(self, index):
        current_widget = self.main_content.widget(index)
        if hasattr(current_widget, "refresh_dashboard"):
            current_widget.refresh_dashboard()
        elif hasattr(current_widget, "load_user_data"):
            current_widget.load_user_data()

    def open_help_dialog(self):
        """دیالوگ راهنمای برنامه را باز می‌کند."""
        dialog = HelpDialog(self)
        dialog.exec()


class AppController:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.auth_window = AuthWindow(self.db_manager)
        self.auth_window.login_successful.connect(self.show_main_window)
        self.main_window = None

    def run(self):
        self.auth_window.show()

    def close(self):
        print("Application is closing.")
        pass

    def show_main_window(self):
        if not self.main_window:
            self.main_window = AppMainWindow()
        self.main_window.show()


def apply_startup_theme(app):
    settings = QSettings("MySoft", "HesabYar")
    theme_value = settings.value("appearance/theme", "light")
    accent_color = settings.value("appearance/accent_color", "#3498db")

    qss_file = resource_path(f"{theme_value}_theme.qss")
    try:
        with open(qss_file, "r", encoding="utf-8") as f:
            template_qss = f.read()

        final_qss = template_qss.replace("{{ACCENT_COLOR}}", accent_color)
        app.setStyleSheet(final_qss)
    except FileNotFoundError:
        print(f"هشدار: فایل تم یافت نشد: {qss_file}")


if __name__ == "__main__":
    initialize_database()

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    apply_startup_theme(app)
    controller = AppController()
    app.aboutToQuit.connect(controller.close)
    controller.run()
    sys.exit(app.exec())
