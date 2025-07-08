# file: pages/invoice_details_page.py
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
    QTextEdit,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor
from utils import resource_path


class InvoiceDetailsPage(QWidget):
    back_requested = Signal()

    def __init__(self, invoice_id, db_manager, parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.db_manager = db_manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        self.title_label = QLabel(
            f"جزئیات فاکتور شماره INV-{self.invoice_id:04d}",
            objectName="dialogTitleLabel",
        )
        back_btn = QPushButton(
            " بازگشت", icon=QIcon(resource_path("assets/icons/arrow-right.svg"))
        )
        back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        details_frame = QFrame(objectName="formDialog")
        self.details_layout = QVBoxLayout(details_frame)
        self.details_layout.addWidget(self.title_label)
        self.form_layout = QFormLayout()
        self.customer_name_label = QLabel()
        self.issue_date_label = QLabel()
        self.status_label = QLabel()
        self.form_layout.addRow("<b>مشتری:</b>", self.customer_name_label)
        self.form_layout.addRow("<b>تاریخ صدور:</b>", self.issue_date_label)
        self.form_layout.addRow("<b>وضعیت:</b>", self.status_label)
        self.details_layout.addLayout(self.form_layout)
        main_layout.addWidget(details_frame)

        main_layout.addWidget(QLabel("اقلام فاکتور:"))
        self.items_table = QTableWidget()
        self.items_table.setMinimumHeight(250)
        self.items_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(
            [
                "شرح",
                "مقدار",
                "قیمت واحد",
                "تخفیف",
                "مالیات",
                "سایر هزینه‌ها",
                "مبلغ نهایی",
            ]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        main_layout.addWidget(self.items_table, 1)

        bottom_frame = QFrame(objectName="formDialog")
        bottom_layout = QHBoxLayout(bottom_frame)
        self.notes_display = QTextEdit(readOnly=True)
        self.notes_display.setMaximumHeight(80)
        notes_v_layout = QVBoxLayout()
        notes_v_layout.addWidget(QLabel("<b>توضیحات فاکتور:</b>"))
        notes_v_layout.addWidget(self.notes_display)

        summary_form = QFormLayout()
        self.total_label = QLabel()
        self.discount_label = QLabel()
        self.tax_label = QLabel()
        self.extra_costs_label = QLabel()
        self.grand_total_label = QLabel(objectName="statValueLabel")
        summary_form.addRow("<b>جمع کل (قبل از تخفیف):</b>", self.total_label)
        summary_form.addRow("<b>مجموع تخفیف:</b>", self.discount_label)
        summary_form.addRow("<b>مجموع مالیات:</b>", self.tax_label)
        summary_form.addRow("<b>مجموع سایر هزینه‌ها:</b>", self.extra_costs_label)
        summary_form.addRow("<b>مبلغ نهایی فاکتور:</b>", self.grand_total_label)

        bottom_layout.addLayout(notes_v_layout, 1)
        bottom_layout.addLayout(summary_form, 1)
        main_layout.addWidget(bottom_frame)

        self.load_invoice_data()

    def load_invoice_data(self):
        invoice_details = self.db_manager.get_invoice_details(self.invoice_id)
        invoice_items = self.db_manager.get_invoice_items(self.invoice_id)
        if not invoice_details:
            return

        invoice_keys = invoice_details.keys()
        self.customer_name_label.setText(invoice_details["customer_name"])
        self.issue_date_label.setText(invoice_details["issue_date"])

        status_text = invoice_details["status"]
        if status_text == "کسری":
            amount_paid = (
                invoice_details["amount_paid"] if "amount_paid" in invoice_keys else 0
            )
            remaining = invoice_details["total_amount"] - (amount_paid or 0)
            status_text = f"کسری (مبلغ باقی‌مانده: {remaining:,.0f} ریال)"
        self.status_label.setText(status_text)

        if hasattr(self, "payment_info_label"):
            self.form_layout.removeRow(self.payment_info_label.parentWidget())

        payment_method = (
            invoice_details["payment_method"]
            if "payment_method" in invoice_keys
            else "نقدی"
        )
        payment_text = payment_method
        if payment_method == "چکی":
            cheque_number = (
                invoice_details["cheque_number"]
                if "cheque_number" in invoice_keys
                else "-"
            )
            cheque_due_date = (
                invoice_details["cheque_due_date"]
                if "cheque_due_date" in invoice_keys
                else "-"
            )
            payment_text += (
                f" (شماره: {cheque_number or '-'} | سررسید: {cheque_due_date or '-'})"
            )

        self.payment_info_label = QLabel(payment_text)
        self.form_layout.addRow("<b>روش پرداخت:</b>", self.payment_info_label)

        notes = (
            invoice_details["notes"]
            if "notes" in invoice_keys
            else "توضیحاتی ثبت نشده است."
        )
        self.notes_display.setPlainText(notes or "")
        self.grand_total_label.setText(f"{invoice_details['total_amount']:,.0f} ریال")

        self.items_table.setRowCount(len(invoice_items))
        (
            total_before_discount,
            total_discount_amount,
            total_tax_amount,
            total_extra_fees,
        ) = (0, 0, 0, 0)

        for row, item in enumerate(invoice_items):
            item_keys = item.keys()
            quantity = item["quantity"] if "quantity" in item_keys else 0
            unit_price = item["unit_price"] if "unit_price" in item_keys else 0
            discount_p = (
                item["discount_percent"] if "discount_percent" in item_keys else 0
            )
            tax_p = item["tax_percent"] if "tax_percent" in item_keys else 0
            extra_costs = item["extra_costs"] if "extra_costs" in item_keys else []

            total_price = quantity * unit_price
            discount_amount = total_price * (discount_p / 100)

            price_after_discount = total_price - discount_amount
            tax_amount = price_after_discount * (tax_p / 100)

            extra_fees_amount = 0
            if isinstance(extra_costs, list):
                for fee in extra_costs:
                    fee_val = fee.get("value", 0)
                    extra_fees_amount += (
                        price_after_discount * (fee_val / 100)
                        if fee.get("type") == "percent"
                        else fee_val
                    )

            final_item_price = price_after_discount + tax_amount + extra_fees_amount
            total_before_discount += total_price
            total_discount_amount += discount_amount
            total_tax_amount += tax_amount
            total_extra_fees += extra_fees_amount

            self.items_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    item["description"] if "description" in item_keys else ""
                ),
            )
            self.items_table.setItem(row, 1, QTableWidgetItem(f"{quantity:g}"))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{unit_price:,.0f}"))
            self.items_table.setItem(
                row, 3, QTableWidgetItem(f"{discount_amount:,.0f} ({discount_p:g}%)")
            )
            self.items_table.setItem(
                row, 4, QTableWidgetItem(f"{tax_amount:,.0f} ({tax_p:g}%)")
            )
            self.items_table.setItem(
                row, 5, QTableWidgetItem(f"{extra_fees_amount:,.0f}")
            )
            self.items_table.setItem(
                row, 6, QTableWidgetItem(f"{final_item_price:,.0f}")
            )

        self.total_label.setText(f"{total_before_discount:,.0f} ریال")
        self.discount_label.setText(f"{total_discount_amount:,.0f} ریال")
        self.tax_label.setText(f"{total_tax_amount:,.0f} ریال")
        self.extra_costs_label.setText(f"{total_extra_fees:,.0f} ریال")
