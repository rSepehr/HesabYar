# file: pages/settings_page.py
import os, csv, json, datetime, traceback, shutil
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QFrame,
    QDialog,
    QTabWidget,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QComboBox,
    QApplication,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QGridLayout,
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QPixmap
from functools import partial
from dialogs.fee_template_dialog import FeeTemplateDialog
from dialogs.account_dialog import AccountDialog
from db_manager import DatabaseManager
from utils import resource_path


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        (
            self.company_info_tab,
            self.accounts_tab,
            self.financial_tab,
            self.appearance_tab,
            self.backup_tab,
        ) = (QWidget(), QWidget(), QWidget(), QWidget(), QWidget())
        self.tabs.addTab(self.company_info_tab, "مشخصات شرکت")
        self.tabs.addTab(self.accounts_tab, "مدیریت حساب‌ها")
        self.tabs.addTab(self.financial_tab, "تنظیمات مالی")
        self.tabs.addTab(self.appearance_tab, "ظاهر برنامه")
        self.tabs.addTab(self.backup_tab, "پشتیبان‌گیری و خروجی")
        self.setup_company_info_tab()
        self.setup_accounts_tab()
        self.setup_financial_tab()
        self.setup_appearance_tab()
        self.setup_backup_tab()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.load_settings()

    def on_tab_changed(self, index):
        if self.tabs.widget(index) == self.accounts_tab:
            self.load_accounts_data()
        elif self.tabs.widget(index) == self.financial_tab:
            self.load_financial_settings()

    def setup_company_info_tab(self):
        tab_layout = QVBoxLayout(self.company_info_tab)
        form_frame = QFrame(objectName="formDialog")
        main_form_layout = QVBoxLayout(form_frame)
        top_section_layout = QHBoxLayout()
        form_layout = QFormLayout()
        (
            self.company_name_input,
            self.company_national_id_input,
            self.company_economic_code_input,
            self.company_phone_input,
            self.company_landline_input,
            self.company_address_input,
            self.company_postal_code_input,
        ) = (
            QLineEdit(),
            QLineEdit(),
            QLineEdit(),
            QLineEdit(),
            QLineEdit(),
            QLineEdit(),
            QLineEdit(),
        )
        form_layout.addRow("نام شرکت/فروشنده:", self.company_name_input)
        form_layout.addRow("شناسه ملی:", self.company_national_id_input)
        form_layout.addRow("کد اقتصادی:", self.company_economic_code_input)
        form_layout.addRow("تلفن همراه:", self.company_phone_input)
        form_layout.addRow("تلفن ثابت:", self.company_landline_input)
        form_layout.addRow("کد پستی:", self.company_postal_code_input)
        form_layout.addRow("آدرس:", self.company_address_input)
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview_label = QLabel("پیش‌نمایش لوگو")
        self.logo_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview_label.setMinimumSize(150, 150)
        self.logo_preview_label.setStyleSheet(
            "border: 1px dashed #aaa; border-radius: 5px;"
        )
        logo_layout.addWidget(self.logo_preview_label)
        top_section_layout.addLayout(form_layout, 3)
        top_section_layout.addLayout(logo_layout, 1)
        main_form_layout.addLayout(top_section_layout)
        bottom_layout = QHBoxLayout()
        self.logo_path_input = QLineEdit(
            readOnly=True, placeholderText="مسیر فایل لوگو..."
        )
        browse_logo_btn = QPushButton("انتخاب لوگو")
        remove_logo_btn = QPushButton("حذف لوگو")
        browse_logo_btn.clicked.connect(self.browse_logo)
        remove_logo_btn.clicked.connect(self.remove_logo)
        bottom_layout.addWidget(self.logo_path_input, 1)
        bottom_layout.addWidget(browse_logo_btn)
        bottom_layout.addWidget(remove_logo_btn)
        main_form_layout.addLayout(bottom_layout)
        tab_layout.addWidget(form_frame)
        save_btn = QPushButton("ذخیره تنظیمات شرکت", objectName="primaryButton")
        save_btn.clicked.connect(self.save_company_settings)
        tab_layout.addWidget(save_btn, 0, Qt.AlignmentFlag.AlignLeft)
        tab_layout.addStretch()

    def save_company_settings(self):
        settings = QSettings("MySoft", "HesabYar")
        settings.beginGroup("company")
        settings.setValue("name", self.company_name_input.text())
        settings.setValue("national_id", self.company_national_id_input.text())
        settings.setValue("economic_code", self.company_economic_code_input.text())
        settings.setValue("phone", self.company_phone_input.text())
        settings.setValue("landline", self.company_landline_input.text())
        settings.setValue("postal_code", self.company_postal_code_input.text())
        settings.setValue("address", self.company_address_input.text())
        settings.setValue("logo_path", self.logo_path_input.text())
        settings.endGroup()
        QMessageBox.information(self, "موفقیت", "تنظیمات شرکت با موفقیت ذخیره شد.")

    def browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب تصویر لوگو", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.logo_path_input.setText(file_path)
            self.update_logo_preview(file_path)

    def remove_logo(self):
        self.logo_path_input.clear()
        self.logo_preview_label.clear()
        self.logo_preview_label.setText("پیش‌نمایش لوگو")

    def update_logo_preview(self, path):
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            self.logo_preview_label.setPixmap(
                pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.logo_preview_label.setText("پیش‌نمایش لوگو")

    def setup_accounts_tab(self):
        layout = QVBoxLayout(self.accounts_tab)
        frame = QFrame(objectName="formDialog")
        frame_layout = QVBoxLayout(frame)
        title = QLabel("مدیریت سرفصل‌های حسابداری")
        frame_layout.addWidget(title)
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(4)
        self.accounts_table.setHorizontalHeaderLabels(
            ["ID", "نام حساب", "نوع", "توضیحات"]
        )
        self.accounts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.accounts_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.accounts_table.setColumnHidden(0, True)
        frame_layout.addWidget(self.accounts_table)
        buttons_layout = QHBoxLayout()
        add_btn, edit_btn, remove_btn = (
            QPushButton("افزودن حساب"),
            QPushButton("ویرایش حساب"),
            QPushButton("حذف حساب"),
        )
        add_btn.clicked.connect(self.add_new_account)
        edit_btn.clicked.connect(self.edit_selected_account)
        remove_btn.clicked.connect(self.remove_selected_account)
        buttons_layout.addStretch()
        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(edit_btn)
        buttons_layout.addWidget(remove_btn)
        frame_layout.addLayout(buttons_layout)
        layout.addWidget(frame)
        layout.addStretch()

    def load_accounts_data(self):
        self.accounts_table.setRowCount(0)
        accounts = self.db_manager.get_all_accounts()
        if not accounts:
            return
        self.accounts_table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            type_text = "درآمد" if account["type"] == "income" else "هزینه"
            self.accounts_table.setItem(row, 0, QTableWidgetItem(str(account["id"])))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account["name"]))
            self.accounts_table.setItem(row, 2, QTableWidgetItem(type_text))
            self.accounts_table.setItem(
                row, 3, QTableWidgetItem(account["description"])
            )

    def add_new_account(self):
        dialog = AccountDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_accounts_data()

    def edit_selected_account(self):
        selected_rows = self.accounts_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطا", "لطفاً یک حساب را برای ویرایش انتخاب کنید.")
            return
        selected_row = selected_rows[0].row()
        account_id = int(self.accounts_table.item(selected_row, 0).text())
        dialog = AccountDialog(self.db_manager, account_id=account_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_accounts_data()

    def remove_selected_account(self):
        selected_rows = self.accounts_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطا", "لطفاً یک حساب را برای حذف انتخاب کنید.")
            return
        selected_row = selected_rows[0].row()
        account_id = int(self.accounts_table.item(selected_row, 0).text())
        account_name = self.accounts_table.item(selected_row, 1).text()
        reply = QMessageBox.question(
            self, "تایید حذف", f"آیا از حذف حساب «{account_name}» مطمئن هستید؟"
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.db_manager.delete_account(account_id)
            if success:
                QMessageBox.information(self, "موفق", msg)
                self.load_accounts_data()
            else:
                QMessageBox.critical(self, "خطا", msg)

    def setup_financial_tab(self):
        layout = QVBoxLayout(self.financial_tab)
        fees_frame = QFrame(objectName="formDialog")
        fees_layout = QVBoxLayout(fees_frame)
        title = QLabel("مدیریت قالب‌های هزینه")
        fees_layout.addWidget(title)
        self.fees_table = QTableWidget()
        self.fees_table.setColumnCount(4)
        self.fees_table.setHorizontalHeaderLabels(["ID", "نام هزینه", "نوع", "مقدار"])
        self.fees_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.fees_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.fees_table.setColumnHidden(0, True)
        fees_layout.addWidget(self.fees_table)
        buttons_layout = QHBoxLayout()
        add_fee_btn, edit_fee_btn, remove_fee_btn = (
            QPushButton("افزودن قالب"),
            QPushButton("ویرایش قالب"),
            QPushButton("حذف قالب"),
        )
        add_fee_btn.clicked.connect(self.add_new_fee_template)
        edit_fee_btn.clicked.connect(self.edit_selected_fee_template)
        remove_fee_btn.clicked.connect(self.remove_selected_fee_template)
        buttons_layout.addStretch()
        buttons_layout.addWidget(add_fee_btn)
        buttons_layout.addWidget(edit_fee_btn)
        buttons_layout.addWidget(remove_fee_btn)
        fees_layout.addLayout(buttons_layout)
        layout.addWidget(fees_frame)
        layout.addStretch()

    def load_financial_settings(self):
        self.fees_table.setRowCount(0)
        templates = self.db_manager.get_fee_templates()
        if not templates:
            return
        self.fees_table.setRowCount(len(templates))
        for row, template in enumerate(templates):
            type_text = "درصدی (%)" if template["type"] == "percent" else "مبلغ ثابت"
            self.fees_table.setItem(row, 0, QTableWidgetItem(str(template["id"])))
            self.fees_table.setItem(row, 1, QTableWidgetItem(template["name"]))
            self.fees_table.setItem(row, 2, QTableWidgetItem(type_text))
            self.fees_table.setItem(row, 3, QTableWidgetItem(str(template["value"])))

    def add_new_fee_template(self):
        dialog = FeeTemplateDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_financial_settings()

    def edit_selected_fee_template(self):
        selected_rows = self.fees_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطا", "لطفاً یک قالب را برای ویرایش انتخاب کنید.")
            return
        selected_row = selected_rows[0].row()
        fee_id = int(self.fees_table.item(selected_row, 0).text())
        dialog = FeeTemplateDialog(self.db_manager, fee_id=fee_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_financial_settings()

    def remove_selected_fee_template(self):
        selected_rows = self.fees_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطا", "لطفاً یک قالب را برای حذف انتخاب کنید.")
            return
        selected_row = selected_rows[0].row()
        fee_id = int(self.fees_table.item(selected_row, 0).text())
        fee_name = self.fees_table.item(selected_row, 1).text()
        reply = QMessageBox.question(
            self, "تایید حذف", f"آیا از حذف قالب هزینه «{fee_name}» مطمئن هستید؟"
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.db_manager.delete_fee_template(fee_id)
            if success:
                QMessageBox.information(self, "موفق", msg)
                self.load_financial_settings()
            else:
                QMessageBox.critical(self, "خطا", msg)

    def setup_appearance_tab(self):
        layout = QVBoxLayout(self.appearance_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        theme_frame = QFrame(objectName="formDialog")
        theme_layout = QFormLayout(theme_frame)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["روشن", "تاریک"])
        self.theme_combo.currentTextChanged.connect(self.save_and_apply_theme)
        theme_layout.addRow("انتخاب تم اصلی برنامه:", self.theme_combo)
        layout.addWidget(theme_frame)
        accent_color_frame = QFrame(objectName="formDialog")
        accent_layout = QVBoxLayout(accent_color_frame)
        accent_layout.addWidget(QLabel("انتخاب رنگ ثانویه برنامه:"))
        self.colors = {
            "آبی (پیش‌فرض)": "#3498db",
            "سبز": "#27ae60",
            "نارنجی": "#e67e22",
            "قرمز": "#e74c3c",
            "بنفش": "#8e44ad",
            "فیروزه‌ای": "#1abc9c",
        }
        color_grid = QGridLayout()
        color_grid.setSpacing(10)
        row, col = 0, 0
        for name, code in self.colors.items():
            btn = QPushButton(name)
            btn.setStyleSheet(
                f"background-color: {code}; color: white; border-radius: 5px; padding: 10px; font-weight: bold;"
            )
            btn.clicked.connect(partial(self.save_and_apply_theme, accent_color=code))
            color_grid.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        accent_layout.addLayout(color_grid)
        layout.addWidget(accent_color_frame)
        layout.addStretch()

    def save_and_apply_theme(self, theme_name=None, accent_color=None):
        settings = QSettings("MySoft", "HesabYar")
        settings.beginGroup("appearance")
        if theme_name:
            theme_map = {"روشن": "light", "تاریک": "dark"}
            theme_value = theme_map.get(theme_name, "light")
            settings.setValue("theme", theme_value)
        else:
            theme_value = settings.value("theme", "light")
        if accent_color:
            settings.setValue("accent_color", accent_color)
        else:
            accent_color = settings.value("accent_color", "#3498db")
        settings.endGroup()
        self.apply_theme_with_accent(theme_value, accent_color)

    def apply_theme_with_accent(self, theme_value, accent_color):
        qss_file = f"{theme_value}_theme.qss"
        try:
            with open(qss_file, "r", encoding="utf-8") as f:
                template_qss = f.read()
            final_qss = template_qss.replace("{{ACCENT_COLOR}}", accent_color)
            QApplication.instance().setStyleSheet(final_qss)
        except FileNotFoundError:
            print(f"فایل تم یافت نشد: {qss_file}")

    def setup_backup_tab(self):
        layout = QVBoxLayout(self.backup_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        backup_frame = QFrame(objectName="formDialog")
        frame_layout = QVBoxLayout(backup_frame)
        title = QLabel("پشتیبان‌گیری و بازیابی اطلاعات")
        frame_layout.addWidget(title)
        description = QLabel(
            "از این بخش می‌توانید یک نسخه کامل از دیتابیس تهیه کرده یا نسخه پشتیبان قبلی را بازیابی کنید."
        )
        description.setWordWrap(True)
        frame_layout.addWidget(description)
        buttons_layout = QHBoxLayout()
        self.backup_btn = QPushButton(
            " تهیه نسخه پشتیبان",
            icon=QIcon(resource_path("assets/icons/download-cloud.svg")),
        )
        self.restore_btn = QPushButton(
            " بازیابی از نسخه پشتیبان",
            icon=QIcon(resource_path("assets/icons/upload-cloud.svg")),
        )
        self.backup_btn.clicked.connect(self.handle_backup)
        self.restore_btn.clicked.connect(self.handle_restore)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.backup_btn)
        buttons_layout.addWidget(self.restore_btn)
        buttons_layout.addStretch()
        frame_layout.addLayout(buttons_layout)
        layout.addWidget(backup_frame)
        export_frame = QFrame(objectName="formDialog")
        export_layout = QVBoxLayout(export_frame)
        export_title = QLabel("خروجی گرفتن از داده‌ها (CSV)")
        export_layout.addWidget(export_title)
        export_desc = QLabel(
            "از این بخش می‌توانید از جدول‌های مختلف به صورت مجزا در فرمت CSV خروجی بگیرید."
        )
        export_desc.setWordWrap(True)
        export_layout.addWidget(export_desc)
        csv_buttons_layout = QGridLayout()
        self.export_customers_btn = QPushButton("خروجی مشتریان")
        self.export_customers_btn.clicked.connect(self.export_customers)
        self.export_products_btn = QPushButton("خروجی کالاها")
        self.export_products_btn.clicked.connect(self.export_products)
        self.export_invoices_btn = QPushButton("خروجی فاکتورها")
        self.export_invoices_btn.clicked.connect(self.export_invoices)
        self.export_expenses_btn = QPushButton("خروجی هزینه‌ها")
        self.export_expenses_btn.clicked.connect(self.export_expenses)
        csv_buttons_layout.addWidget(self.export_customers_btn, 0, 0)
        csv_buttons_layout.addWidget(self.export_products_btn, 0, 1)
        csv_buttons_layout.addWidget(self.export_invoices_btn, 1, 0)
        csv_buttons_layout.addWidget(self.export_expenses_btn, 1, 1)
        export_layout.addLayout(csv_buttons_layout)
        layout.addWidget(export_frame)
        layout.addStretch()

    def handle_backup(self):
        db_path = self.db_manager.db_name
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "خطا", "فایل دیتابیس یافت نشد!")
            return
        today_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_filename = os.path.join(
            os.path.expanduser("~"), f"hesabyar_backup_{today_str}.db"
        )
        save_path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره فایل پشتیبان", default_filename, "Database Files (*.db)"
        )
        if save_path:
            try:
                shutil.copy(db_path, save_path)
                QMessageBox.information(
                    self,
                    "موفقیت",
                    f"نسخه پشتیبان با موفقیت در مسیر زیر ذخیره شد:\n{save_path}",
                )
            except Exception as e:
                QMessageBox.critical(self, "خطا در پشتیبان‌گیری", f"خطایی رخ داد: {e}")

    def handle_restore(self):
        db_path = self.db_manager.db_name
        warning_message = "توجه!\nاین عمل تمام اطلاعات فعلی شما را حذف کرده و اطلاعات فایل پشتیبان را جایگزین آن می‌کند.\nاین عمل غیرقابل بازگشت است.\nآیا از ادامه کار مطمئن هستید؟"
        reply = QMessageBox.critical(
            self,
            "هشدار جدی!",
            warning_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "لغو شد", "عملیات بازیابی لغو شد.")
            return
        restore_path, _ = QFileDialog.getOpenFileName(
            self,
            "انتخاب فایل پشتیبان برای بازیابی",
            os.path.expanduser("~"),
            "Database Files (*.db)",
        )
        if not restore_path:
            return
        try:
            shutil.copy(restore_path, db_path)
            QMessageBox.information(
                self,
                "موفقیت",
                "اطلاعات با موفقیت بازیابی شد.\nلطفاً برای اعمال تغییرات، برنامه را ببندید و دوباره اجرا کنید.",
            )
        except Exception as e:
            QMessageBox.critical(
                self, "خطا در بازیابی", f"خطایی در هنگام بازیابی اطلاعات رخ داد: {e}"
            )

    def _export_data_to_csv(self, data_method, table_name, file_path):
        try:
            data_list = data_method()
            if not data_list:
                QMessageBox.information(
                    self,
                    "اطلاعاتی وجود ندارد",
                    f"هیچ داده‌ای در جدول '{table_name}' برای خروجی گرفتن ثبت نشده است.",
                )
                return False
            headers = data_list[0].keys()
            with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                for item in data_list:
                    row_values = []
                    for key in headers:
                        value = item.get(key)
                        row_values.append(
                            json.dumps(value, ensure_ascii=False)
                            if isinstance(value, (dict, list))
                            else str(value) if value is not None else ""
                        )
                    writer.writerow(row_values)
            return True
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطا در ذخیره‌سازی",
                f"خطایی در هنگام ذخیره فایل '{os.path.basename(file_path)}' رخ داد:\n{traceback.format_exc()}",
            )
            return False

    def export_customers(self):
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        default_filename = f"مشتریان_export_{today_str}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره فایل خروجی مشتریان",
            default_filename,
            "CSV Files (*.csv);;All Files (*)",
        )
        if file_path and self._export_data_to_csv(
            self.db_manager.get_all_customers, "مشتریان", file_path
        ):
            QMessageBox.information(
                self,
                "موفقیت",
                f"اطلاعات مشتریان با موفقیت در فایل زیر ذخیره شد:\n{file_path}",
            )

    def export_products(self):
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        default_filename = f"کالاها_export_{today_str}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره فایل خروجی کالاها",
            default_filename,
            "CSV Files (*.csv);;All Files (*)",
        )
        if file_path and self._export_data_to_csv(
            self.db_manager.get_all_products, "کالاها", file_path
        ):
            QMessageBox.information(
                self,
                "موفقیت",
                f"اطلاعات کالاها با موفقیت در فایل زیر ذخیره شد:\n{file_path}",
            )

    def export_expenses(self):
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        default_filename = f"هزینه‌ها_export_{today_str}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره فایل خروجی هزینه‌ها",
            default_filename,
            "CSV Files (*.csv);;All Files (*)",
        )
        if file_path and self._export_data_to_csv(
            self.db_manager.get_all_expenses, "هزینه‌ها", file_path
        ):
            QMessageBox.information(
                self,
                "موفقیت",
                f"اطلاعات هزینه‌ها با موفقیت در فایل زیر ذخیره شد:\n{file_path}",
            )

    def export_invoices(self):
        invoices = self.db_manager.get_all_invoices()
        if not invoices:
            QMessageBox.information(
                self,
                "اطلاعاتی وجود ندارد",
                "هیچ فاکتوری برای خروجی گرفتن ثبت نشده است.",
            )
            return
        folder_path = QFileDialog.getExistingDirectory(
            self, "انتخاب پوشه برای ذخیره فایل‌های خروجی فاکتورها"
        )
        if not folder_path:
            return
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        invoices_path = os.path.join(folder_path, f"فاکتورها_{today_str}.csv")
        items_path = os.path.join(folder_path, f"اقلام_فاکتورها_{today_str}.csv")
        success1 = self._export_data_to_csv(lambda: invoices, "فاکتورها", invoices_path)
        success2 = True
        invoice_items = self.db_manager.get_all_invoice_items()
        if invoice_items:
            success2 = self._export_data_to_csv(
                lambda: invoice_items, "اقلام_فاکتورها", items_path
            )
        if success1 and success2:
            QMessageBox.information(
                self,
                "موفقیت",
                f"فایل‌های خروجی با موفقیت در پوشه زیر ذخیره شدند:\n{folder_path}",
            )

    def load_settings(self):
        settings = QSettings("MySoft", "HesabYar")
        settings.beginGroup("company")
        self.company_name_input.setText(settings.value("name", ""))
        self.company_national_id_input.setText(settings.value("national_id", ""))
        self.company_economic_code_input.setText(settings.value("economic_code", ""))
        self.company_phone_input.setText(settings.value("phone", ""))
        self.company_landline_input.setText(settings.value("landline", ""))
        self.company_postal_code_input.setText(settings.value("postal_code", ""))
        self.company_address_input.setText(settings.value("address", ""))
        logo_path = settings.value("logo_path", "")
        self.logo_path_input.setText(logo_path)
        self.update_logo_preview(logo_path)
        settings.endGroup()

        self.on_tab_changed(self.tabs.currentIndex())

        settings.beginGroup("appearance")
        theme_value = settings.value("theme", "light")
        theme_map = {"روشن": "light", "تاریک": "dark"}
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(theme_map.get(theme_value, "روشن"))
        self.theme_combo.blockSignals(False)
        settings.endGroup()
