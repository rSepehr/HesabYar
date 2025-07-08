# file: dialogs/invoice_dialog.py
import jdatetime
import json
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QTextEdit,
    QMessageBox,
    QWidget,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QIcon

from signal_bus import signal_bus
from dialogs.customer_dialog import CustomerDialog
from dialogs.cheque_info_dialog import ChequeInfoDialog
from utils import resource_path


class InvoiceDialog(QDialog):
    def __init__(self, db_manager, invoice_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.invoice_id = invoice_id
        self.products_list = []
        self.fee_templates = []

        self.setWindowTitle("صدور / ویرایش فاکتور")
        self.setMinimumSize(1000, 750)
        self.setObjectName("formDialog")

        main_layout = QVBoxLayout(self)
        top_frame = QFrame(objectName="formDialog")
        top_hbox_layout = QHBoxLayout(top_frame)

        right_form_layout = QFormLayout()
        customer_layout = QHBoxLayout()
        self.customer_combo = QComboBox(editable=True)
        self.add_customer_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/plus.svg")), text=""
        )
        self.add_customer_btn.setToolTip("افزودن مشتری جدید")
        self.add_customer_btn.setFixedWidth(40)
        customer_layout.addWidget(self.customer_combo, 1)
        customer_layout.addWidget(self.add_customer_btn)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["پرداخت نشده", "پرداخت شده", "کسری"])
        right_form_layout.addRow("مشتری:", customer_layout)
        right_form_layout.addRow("وضعیت فاکتور:", self.status_combo)

        left_form_layout = QFormLayout()
        self.issue_date_edit = QLineEdit(jdatetime.date.today().strftime("%Y/%m/%d"))
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["نقدی", "چکی", "حواله بانکی"])
        left_form_layout.addRow("تاریخ صدور:", self.issue_date_edit)
        left_form_layout.addRow("روش پرداخت:", self.payment_method_combo)

        top_hbox_layout.addLayout(left_form_layout)
        top_hbox_layout.addLayout(right_form_layout)
        main_layout.addWidget(top_frame)

        main_layout.addWidget(QLabel("اقلام فاکتور:"))
        self.items_table = QTableWidget()
        self.items_table.setMinimumHeight(150)
        self.items_table.setColumnCount(10)
        self.items_table.setHorizontalHeaderLabels(
            [
                "شرح کالا/خدمات",
                "مقدار",
                "مبلغ واحد",
                "مبلغ کل",
                "درصد تخفیف",
                "مبلغ تخفیف",
                "مبلغ پس از تخفیف",
                "درصد مالیات",
                "مبلغ مالیات",
                "سایر هزینه‌ها",
            ]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.items_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        main_layout.addWidget(self.items_table, 1)

        table_buttons_layout = QHBoxLayout()
        self.add_item_btn = QPushButton("افزودن کالا")
        self.add_fee_btn = QPushButton("افزودن هزینه دیگر")
        self.remove_item_btn = QPushButton("حذف ردیف")
        table_buttons_layout.addWidget(self.add_item_btn)
        table_buttons_layout.addWidget(self.add_fee_btn)
        table_buttons_layout.addWidget(self.remove_item_btn)
        table_buttons_layout.addStretch()
        main_layout.addLayout(table_buttons_layout)

        bottom_frame = QFrame(objectName="formDialog")
        bottom_layout = QHBoxLayout(bottom_frame)
        self.notes_edit = QTextEdit(placeholderText="توضیحات فاکتور (اختیاری)")

        summary_layout = QFormLayout()
        self.total_sum_label = QLabel("۰ ریال")
        self.discount_sum_label = QLabel("۰ ریال")
        self.total_after_discount_sum_label = QLabel("۰ ریال")
        self.tax_sum_label = QLabel("۰ ریال")
        self.other_fees_sum_label = QLabel("۰ ریال")
        self.grand_total_label = QLabel("۰ ریال")
        self.grand_total_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        summary_layout.addRow("جمع کل:", self.total_sum_label)
        summary_layout.addRow("جمع تخفیف:", self.discount_sum_label)
        summary_layout.addRow("جمع پس از تخفیف:", self.total_after_discount_sum_label)
        summary_layout.addRow("جمع مالیات:", self.tax_sum_label)
        summary_layout.addRow("جمع سایر هزینه‌ها:", self.other_fees_sum_label)
        summary_layout.addRow("<b>مبلغ نهایی قابل پرداخت:</b>", self.grand_total_label)

        bottom_layout.addWidget(self.notes_edit, 1)
        bottom_layout.addLayout(summary_layout, 1)
        main_layout.addWidget(bottom_frame)

        final_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("ذخیره فاکتور", objectName="primaryButton")
        self.cancel_button = QPushButton("لغو", clicked=self.reject)
        final_buttons_layout.addStretch()
        final_buttons_layout.addWidget(self.save_button)
        final_buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(final_buttons_layout)

        self.items_table.cellChanged.connect(self.update_row_calculations)
        self.add_item_btn.clicked.connect(self.add_product_row)
        self.add_fee_btn.clicked.connect(self.add_extra_fee_to_row)
        self.remove_item_btn.clicked.connect(self.remove_selected_row)
        self.save_button.clicked.connect(self.process_and_save_invoice)
        self.add_customer_btn.clicked.connect(self.quick_add_customer)
        signal_bus.customer_saved.connect(self.refresh_customer_list)

        self.load_initial_data()

    def process_and_save_invoice(self):
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            QMessageBox.warning(self, "خطا", "لطفاً یک مشتری انتخاب کنید.")
            return
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "خطا", "فاکتور باید حداقل شامل یک قلم کالا باشد.")
            return

        grand_total = float(
            self.grand_total_label.text().replace(" ریال", "").replace(",", "")
        )
        status = self.status_combo.currentText()
        payment_method = self.payment_method_combo.currentText()
        amount_paid = 0
        cheque_info = {}

        if status == "کسری":
            paid, ok = QInputDialog.getDouble(
                self,
                "مبلغ پرداختی",
                "مبلغ پرداخت شده را وارد کنید:",
                0,
                0,
                grand_total,
                0,
            )
            if not ok:
                return
            amount_paid = paid
        elif status == "پرداخت شده":
            amount_paid = grand_total

        if payment_method == "چکی":
            cheque_dialog = ChequeInfoDialog(self)
            if cheque_dialog.exec() == QDialog.DialogCode.Accepted:
                cheque_info = cheque_dialog.get_data()
                if not cheque_info or not cheque_info.get("number"):
                    QMessageBox.warning(self, "خطا", "شماره چک الزامی است.")
                    return
            else:
                return

        invoice_data = {
            "customer_id": customer_id,
            "issue_date": self.issue_date_edit.text(),
            "notes": self.notes_edit.toPlainText(),
            "total_amount": grand_total,
            "status": status,
            "amount_paid": amount_paid,
            "payment_method": payment_method,
            "payment_date": (
                self.issue_date_edit.text() if status == "پرداخت شده" else None
            ),
            "cheque_number": cheque_info.get("number"),
            "cheque_due_date": cheque_info.get("due_date"),
        }

        items_data_to_save = []
        products_to_update_stock = []
        for row in range(self.items_table.rowCount()):
            try:
                p_data_container = self.items_table.item(row, 0).data(
                    Qt.ItemDataRole.UserRole
                )
                quantity_sold = float(self.items_table.item(row, 1).text())
                cogs_for_this_item = 0

                if p_data_container and p_data_container.get("type") == "product":
                    product_info = p_data_container["data"]
                    product_id = product_info["id"]
                    products_to_update_stock.append(
                        {"id": product_id, "quantity": quantity_sold}
                    )

                    full_product_details = self.db_manager.get_product_by_id(product_id)
                    if full_product_details:
                        avg_price = full_product_details["average_purchase_price"] or 0
                        cogs_for_this_item = quantity_sold * avg_price

                extra_costs_list = [
                    dict(fee) for fee in p_data_container.get("extra_costs", [])
                ]
                item_dict = {
                    "description": self.items_table.item(row, 0).text(),
                    "quantity": quantity_sold,
                    "unit": product_info["unit"],
                    "unit_price": float(self.items_table.item(row, 2).text()),
                    "discount_percent": float(self.items_table.item(row, 4).text()),
                    "tax_percent": float(self.items_table.item(row, 7).text()),
                    "extra_costs": extra_costs_list,
                    "cost_of_good_sold": cogs_for_this_item,
                }
                items_data_to_save.append(item_dict)
            except (ValueError, TypeError, AttributeError, KeyError) as e:
                QMessageBox.warning(
                    self,
                    "خطا در ردیف",
                    f"اطلاعات ردیف {row + 1} ناقص یا نامعتبر است.\n{e}",
                )
                return

        success, msg, new_invoice_id = self.db_manager.save_invoice(
            invoice_data, items_data_to_save
        )

        if success:
            for product in products_to_update_stock:
                update_success, update_msg = self.db_manager.decrease_product_stock(
                    product["id"], product["quantity"]
                )
                if not update_success:
                    QMessageBox.warning(self, "خطای انبار", update_msg)

            if payment_method == "چکی":
                cheque_amount = grand_total
                cheque_data = {
                    "type": "دریافتی",
                    "cheque_number": cheque_info["number"],
                    "bank_name": cheque_info["bank"],
                    "amount": cheque_amount,
                    "issue_date": invoice_data["issue_date"],
                    "due_date": cheque_info["due_date"],
                    "status": "در انتظار وصول",
                    "description": f"مربوط به فاکتور شماره {new_invoice_id}",
                    "invoice_id": new_invoice_id,
                }
                cheque_success, cheque_msg = self.db_manager.add_cheque(cheque_data)
                if cheque_success:
                    QMessageBox.information(
                        self,
                        "ثبت چک",
                        f"چک به شماره {cheque_info['number']} با موفقیت ثبت شد.",
                    )
                else:
                    QMessageBox.critical(self, "خطا در ثبت چک", cheque_msg)

            QMessageBox.information(self, "موفقیت", msg)
            signal_bus.invoice_saved.emit()
            signal_bus.product_saved.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "خطا در ذخیره‌سازی", msg)

    def quick_add_customer(self):
        dialog = CustomerDialog(self.db_manager, parent=self)
        dialog.exec()

    def refresh_customer_list(self):
        current_id = self.customer_combo.currentData()
        self.customer_combo.blockSignals(True)
        self.customer_combo.clear()
        customers = self.db_manager.get_all_customers()
        for c in customers:
            self.customer_combo.addItem(c["name"], userData=c["id"])
        index = self.customer_combo.findData(current_id)
        if index != -1:
            self.customer_combo.setCurrentIndex(index)
        self.customer_combo.blockSignals(False)

    def load_initial_data(self):
        self.refresh_customer_list()
        self.products_list = self.db_manager.get_all_products()
        self.fee_templates = self.db_manager.get_fee_templates()

    def add_product_row(self):
        product_names = [p["name"] for p in self.products_list]
        if not product_names:
            QMessageBox.warning(self, "خطا", "هیچ کالایی در سیستم تعریف نشده است.")
            return
        product_name, ok = QInputDialog.getItem(
            self, "انتخاب کالا", "کالا:", product_names, 0, False
        )
        if ok and product_name:
            p_data = next(
                (p for p in self.products_list if p["name"] == product_name), None
            )
            if not p_data:
                return
            self.items_table.blockSignals(True)
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(p_data["name"]))
            self.items_table.setItem(row, 1, QTableWidgetItem("1"))
            self.items_table.setItem(
                row, 2, QTableWidgetItem(str(int(p_data["unit_price"])))
            )
            self.items_table.setItem(row, 4, QTableWidgetItem("0"))
            self.items_table.setItem(row, 7, QTableWidgetItem("9"))
            self.items_table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole,
                {"type": "product", "data": p_data, "extra_costs": []},
            )
            self.items_table.blockSignals(False)
            self.update_row_calculations(row, 1)

    def add_extra_fee_to_row(self):
        row = self.items_table.currentRow()
        item_widget = self.items_table.item(row, 0)
        if (
            row < 0
            or not item_widget
            or item_widget.data(Qt.ItemDataRole.UserRole).get("type") != "product"
        ):
            QMessageBox.warning(
                self, "خطا", "لطفاً ابتدا یک ردیف **کالا** را انتخاب کنید."
            )
            return
        fee_names = [f["name"] for f in self.fee_templates]
        if not fee_names:
            QMessageBox.warning(
                self, "خطا", "هیچ قالب هزینه‌ای در تنظیمات تعریف نشده است."
            )
            return
        fee_name, ok = QInputDialog.getItem(
            self, "انتخاب هزینه", "هزینه:", fee_names, 0, False
        )
        if ok and fee_name:
            fee_data = next(
                (f for f in self.fee_templates if f["name"] == fee_name), None
            )
            item_data = self.items_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            item_data["extra_costs"].append(dict(fee_data))
            self.items_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, item_data)
            self.update_row_calculations(row, 1)

    def remove_selected_row(self):
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_table.removeRow(current_row)
            self.update_summary_totals()

    def update_row_calculations(self, row, column):
        if column not in [1, 2, 4, 7]:
            return

        p_data_container = self.items_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        is_product = p_data_container and p_data_container.get("type") == "product"

        try:
            quantity = float(self.items_table.item(row, 1).text())

            if is_product:
                available_stock = p_data_container["data"]["stock_quantity"]
                if quantity > available_stock:
                    QMessageBox.warning(
                        self,
                        "موجودی ناکافی",
                        f"تنها {available_stock} عدد از این کالا در انبار موجود است. امکان فروش تعداد بیشتر وجود ندارد.",
                    )
                    self.items_table.blockSignals(True)
                    self.items_table.item(row, 1).setText(str(available_stock))
                    self.items_table.blockSignals(False)
                    quantity = available_stock

            self.items_table.blockSignals(True)
            unit_price = float(self.items_table.item(row, 2).text())
            discount_percent = float(self.items_table.item(row, 4).text())
            tax_percent = float(self.items_table.item(row, 7).text())

            total_amount = quantity * unit_price
            discount_amount = total_amount * (discount_percent / 100)
            total_after_discount = total_amount - discount_amount
            tax_amount = total_after_discount * (tax_percent / 100)

            extra_fees_sum = 0
            tooltip_text = ""
            if p_data_container and "extra_costs" in p_data_container:
                for fee in p_data_container["extra_costs"]:
                    fee_amount = (
                        fee["value"]
                        if fee["type"] == "amount"
                        else total_after_discount * (fee["value"] / 100)
                    )
                    extra_fees_sum += fee_amount
                    tooltip_text += f"{fee['name']}: {fee_amount:,.0f} ریال\n"

            def create_readonly_item(text, tooltip=None):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setForeground(QColor("gray"))
                if tooltip:
                    item.setToolTip(tooltip)
                return item

            self.items_table.setItem(
                row, 3, create_readonly_item(f"{total_amount:,.0f}")
            )
            self.items_table.setItem(
                row, 5, create_readonly_item(f"{discount_amount:,.0f}")
            )
            self.items_table.setItem(
                row, 6, create_readonly_item(f"{total_after_discount:,.0f}")
            )
            self.items_table.setItem(row, 8, create_readonly_item(f"{tax_amount:,.0f}"))
            self.items_table.setItem(
                row,
                9,
                create_readonly_item(f"{extra_fees_sum:,.0f}", tooltip_text.strip()),
            )

        except (ValueError, TypeError, AttributeError):
            pass
        finally:
            self.items_table.blockSignals(False)

        self.update_summary_totals()

    def update_summary_totals(self):
        total_sum, discount_sum, total_after_discount_sum, tax_sum, other_fees_sum = (
            0,
            0,
            0,
            0,
            0,
        )
        for row in range(self.items_table.rowCount()):
            try:
                total_sum += float(
                    self.items_table.item(row, 3).text().replace(",", "")
                )
                discount_sum += float(
                    self.items_table.item(row, 5).text().replace(",", "")
                )
                total_after_discount_sum += float(
                    self.items_table.item(row, 6).text().replace(",", "")
                )
                tax_sum += float(self.items_table.item(row, 8).text().replace(",", ""))
                other_fees_sum += float(
                    self.items_table.item(row, 9).text().replace(",", "")
                )
            except (ValueError, TypeError, AttributeError):
                continue
        grand_total = total_after_discount_sum + tax_sum + other_fees_sum
        self.total_sum_label.setText(f"{total_sum:,.0f} ریال")
        self.discount_sum_label.setText(f"{discount_sum:,.0f} ریال")
        self.total_after_discount_sum_label.setText(
            f"{total_after_discount_sum:,.0f} ریال"
        )
        self.tax_sum_label.setText(f"{tax_sum:,.0f} ریال")
        self.other_fees_sum_label.setText(f"{other_fees_sum:,.0f} ریال")
        self.grand_total_label.setText(f"{grand_total:,.0f} ریال")
