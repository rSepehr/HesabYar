# file: pages/reports_page.py
import jdatetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QTextEdit,
    QFormLayout,
    QLineEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from signal_bus import signal_bus


class ReportsPage(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setSpacing(20)

        profit_loss_frame = QFrame(objectName="formDialog")
        profit_loss_layout = QVBoxLayout(profit_loss_frame)

        profit_loss_title = QLabel("گزارش سود و زیان", objectName="dialogTitleLabel")
        profit_loss_layout.addWidget(profit_loss_title)

        date_range_layout = QHBoxLayout()
        date_range_layout.setSpacing(10)

        today_str = jdatetime.date.today().strftime("%Y/%m/%d")
        first_of_month_str = jdatetime.date.today().replace(day=1).strftime("%Y/%m/%d")

        self.start_date_input = QLineEdit(first_of_month_str)
        self.end_date_input = QLineEdit(today_str)

        self.generate_profit_loss_btn = QPushButton("تهیه گزارش")
        self.generate_profit_loss_btn.clicked.connect(self.generate_profit_loss_report)

        date_range_layout.addWidget(QLabel("از تاریخ:"))
        date_range_layout.addWidget(self.start_date_input)
        date_range_layout.addWidget(QLabel("تا تاریخ:"))
        date_range_layout.addWidget(self.end_date_input)
        date_range_layout.addStretch()
        date_range_layout.addWidget(self.generate_profit_loss_btn)

        profit_loss_layout.addLayout(date_range_layout)
        main_layout.addWidget(profit_loss_frame)

        report_frame = QFrame(objectName="formDialog")
        report_layout = QVBoxLayout(report_frame)
        report_title = QLabel("گزارش‌های عمومی", objectName="dialogTitleLabel")
        report_layout.addWidget(report_title)

        form_layout = QFormLayout()
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(
            ["خلاصه عملکرد مالی", "دفتر روزنامه", "لیست کامل فاکتورها", "لیست مشتریان"]
        )
        form_layout.addRow("نوع گزارش:", self.report_type_combo)

        self.generate_report_btn = QPushButton(
            " نمایش گزارش", objectName="primaryButton"
        )
        self.generate_report_btn.clicked.connect(self.generate_general_report)

        report_layout.addLayout(form_layout)
        report_layout.addWidget(self.generate_report_btn, 0, Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(report_frame)

        self.result_display = QTextEdit(readOnly=True)
        self.result_display.setFont(QFont("Vazirmatn-Regular", 11))
        main_layout.addWidget(QLabel("نتیجه گزارش:"))
        main_layout.addWidget(self.result_display, 1)

        signal_bus.invoice_saved.connect(self.refresh_dashboard)
        signal_bus.customer_saved.connect(self.refresh_dashboard)
        self.refresh_dashboard()

    def refresh_dashboard(self):
        """این متد برای سازگاری با سیگنال‌ها باقی مانده و در آینده می‌تواند آمارها را رفرش کند."""
        pass

    def generate_profit_loss_report(self):
        """گزارش نهایی سود و زیان را با تمام جزئیات نمایش می‌دهد."""
        start_date = self.start_date_input.text().strip()
        end_date = self.end_date_input.text().strip()
        if not start_date or not end_date:
            QMessageBox.warning(self, "خطا", "لطفاً تاریخ شروع و پایان را مشخص کنید.")
            return

        try:
            data = self.db_manager.get_detailed_financial_summary(start_date, end_date)

            html = f"""<h3 align="center">گزارش سود و زیان نهایی</h3>
                      <p align="center">از تاریخ {start_date} تا {end_date}</p><hr>"""

            # بخش درآمدها
            html += '<h4 align="right" style="color:#27ae60;">بخش فروش:</h4><ul style="direction:rtl; margin-right: 20px;">'
            if data["revenue_by_account"]:
                for item in data["revenue_by_account"]:
                    html += f"<li><b>{item['account_name']}:</b> {item['total']:,.0f} ریال</li>"
            else:
                html += "<li>هیچ درآمدی در این بازه ثبت نشده است.</li>"
            html += f'</ul><p align="right" style="font-size:14px;"><b>جمع کل درآمد: {data["total_revenue"]:,.0f} ریال</b></p>'

            # بهای تمام شده
            html += f"""<p align="right" style="font-size:14px; color:red;">
                        <b>(-) بهای تمام شده کالای فروش رفته: {data["cogs"]:,.0f} ریال</b></p><hr>"""

            # سود ناخالص
            gross_profit_color = "#2980b9" if data["gross_profit"] >= 0 else "#c0392b"
            html += f"""<p align="right" style="font-size:15px;">
                        <b style="color:{gross_profit_color};">سود ناخالص: {data["gross_profit"]:,.0f} ریال</b></p><hr>"""

            # هزینه‌های عملیاتی
            html += '<h4 align="right" style="color:#c0392b;">هزینه‌های عملیاتی:</h4><ul style="direction:rtl; margin-right: 20px;">'
            if data["expenses_by_account"]:
                for item in data["expenses_by_account"]:
                    html += f"<li><b>{item['account_name']}:</b> {item['total']:,.0f} ریال</li>"
            else:
                html += "<li>هیچ هزینه عملیاتی در این بازه ثبت نشده است.</li>"
            html += f'</ul><p align="right" style="font-size:14px;"><b>جمع هزینه‌های عملیاتی: {data["total_operational_expenses"]:,.0f} ریال</b></p><hr>'

            # سود خالص نهایی
            net_profit_color = "#27ae60" if data["net_profit"] >= 0 else "#c0392b"
            html += f"""<p align="center" style="font-size:18px;">
                        <b>سود / زیان خالص: 
                        <span style="color:{net_profit_color}; font-weight:bold;">{data["net_profit"]:,.0f} ریال</span>
                        </b></p>"""

            self.result_display.setHtml(html)

        except Exception as e:
            import traceback

            traceback.print_exc()
            QMessageBox.critical(self, "خطا در تهیه گزارش", str(e))
            self.result_display.setText(f"خطا در تولید گزارش: {e}")

    def generate_general_report(self):
        """گزارش‌های عمومی را تولید می‌کند."""
        report_type = self.report_type_combo.currentText()
        if report_type == "خلاصه عملکرد مالی":
            self.generate_financial_summary()
        elif report_type == "دفتر روزنامه":
            self.generate_journal_report()
        elif report_type == "لیست کامل فاکتورها":
            self.generate_invoices_list_report()
        elif report_type == "لیست مشتریان":
            self.generate_customers_list_report()

    def generate_financial_summary(self):
        try:
            summary = self.db_manager.get_financial_summary()
            report_text = f"""<h3 align="center">خلاصه عملکرد مالی کل</h3>
                                 <p align="right" style="font-size:14px; direction:rtl;"><b>کل درآمد وصول شده:</b> {summary.get("total_income", 0):,.0f} ریال</p>
                                 <p align="right" style="font-size:14px; direction:rtl;"><b>کل هزینه‌های ثبت شده:</b> {summary.get("total_expenses", 0):,.0f} ریال</p>
                                 <p align="right" style="font-size:14px; direction:rtl;"><b>مجموع طلب‌ها از فاکتورها:</b> {summary.get("total_receivables", 0):,.0f} ریال</p>"""
            self.result_display.setHtml(report_text)
        except Exception as e:
            self.result_display.setText(f"خطا در تولید گزارش: {e}")

    def generate_invoices_list_report(self):
        try:
            invoices = self.db_manager.get_all_invoices()
            if not invoices:
                self.result_display.setText("هیچ فاکتوری برای نمایش وجود ندارد.")
                return
            html = """<h3 align="center">لیست کامل فاکتورها</h3>
                      <table width="100%" border="1" cellspacing="0" cellpadding="5" style="direction:rtl; font-size:13px;">
                      <tr><th>شماره</th><th>مشتری</th><th>تاریخ</th><th>مبلغ کل</th><th>وضعیت</th></tr>"""
            for inv in invoices:
                status_text, status_color = "", "black"
                if inv["status"] == "Paid":
                    status_text, status_color = "پرداخت شده", "#2ecc71"
                elif inv["status"] == "Partially Paid":
                    status_text, status_color = (
                        f"کسری: {inv['total_amount'] - inv['amount_paid']:,.0f}",
                        "#f39c12",
                    )
                else:
                    status_text, status_color = "پرداخت نشده", "#e74c3c"
                html += f"""<tr><td>INV-{inv['id']:04d}</td><td>{inv['customer_name']}</td><td>{inv['issue_date']}</td>
                                <td>{inv['total_amount']:,.0f} ریال</td><td style="color:{status_color};">{status_text}</td></tr>"""
            html += "</table>"
            self.result_display.setHtml(html)
        except Exception as e:
            self.result_display.setText(f"خطا در تولید گزارش: {e}")

    def generate_customers_list_report(self):
        try:
            customers = self.db_manager.get_all_customers()
            if not customers:
                self.result_display.setText("هیچ مشتری برای نمایش وجود ندارد.")
                return

            html = """<h3 align="center">لیست کامل مشتریان</h3>
                      <table width="100%" border="1" cellspacing="0" cellpadding="5" style="direction:rtl; font-size:13px;">
                      <tr><th>نام</th><th>کد/شناسه ملی</th><th>تلفن</th><th>ایمیل</th><th>آدرس</th></tr>"""
            for customer in customers:
                html += f"""<tr>
                                <td>{customer['name'] or ''}</td>
                                <td>{customer['national_id'] or ''}</td>
                                <td>{customer['phone'] or ''}</td>
                                <td>{customer['email'] or ''}</td>
                                <td>{customer['address'] or ''}</td>
                           </tr>"""
            html += "</table>"
            self.result_display.setHtml(html)
        except Exception as e:
            self.result_display.setText(f"خطا در تولید گزارش: {e}")

    def generate_journal_report(self):
        """گزارش دفتر روزنامه را برای بازه زمانی انتخابی تولید و نمایش می‌دهد."""
        start_date = self.start_date_input.text().strip()
        end_date = self.end_date_input.text().strip()

        if not start_date or not end_date:
            QMessageBox.warning(self, "خطا", "لطفاً تاریخ شروع و پایان را مشخص کنید.")
            return

        try:
            transactions = self.db_manager.get_general_journal(start_date, end_date)
            if not transactions:
                self.result_display.setText("هیچ تراکنشی در این بازه زمانی یافت نشد.")
                return

            html = f"""<h3 align="center">دفتر روزنامه</h3>
                      <p align="center">از تاریخ {start_date} تا {end_date}</p>
                      <table width="100%" border="1" cellspacing="0" cellpadding="5" style="direction:rtl; font-size:13px;">
                      <tr>
                          <th>تاریخ</th>
                          <th>شرح تراکنش</th>
                          <th>درآمد (ریال)</th>
                          <th>هزینه (ریال)</th>
                      </tr>"""

            total_income = 0
            total_expense = 0

            for trans in transactions:
                total_income += trans["income"]
                total_expense += trans["expense"]
                income_str = (
                    f"<span style='color:green;'>{trans['income']:,.0f}</span>"
                    if trans["income"]
                    else "۰"
                )
                expense_str = (
                    f"<span style='color:red;'>{trans['expense']:,.0f}</span>"
                    if trans["expense"]
                    else "۰"
                )

                html += f"""<tr>
                                <td align="center">{trans['date']}</td>
                                <td>{trans['description']}</td>
                                <td align="center">{income_str}</td>
                                <td align="center">{expense_str}</td>
                           </tr>"""

            html += f"""<tr>
                            <td colspan="2" align="center"><b>جمع کل</b></td>
                            <td align="center"><b><span style='color:green;'>{total_income:,.0f}</span></b></td>
                            <td align="center"><b><span style='color:red;'>{total_expense:,.0f}</span></b></td>
                       </tr>"""

            html += "</table>"
            self.result_display.setHtml(html)

        except Exception as e:
            self.result_display.setText(f"خطا در تولید گزارش دفتر روزنامه: {e}")
