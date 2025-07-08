# file: pages/purchase_invoice_details_page.py
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
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from utils import resource_path


class PurchaseInvoiceDetailsPage(QWidget):
    back_requested = Signal()

    def __init__(self, purchase_invoice_id, db_manager, parent=None):
        super().__init__(parent)
        self.purchase_invoice_id = purchase_invoice_id
        self.db_manager = db_manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        self.title_label = QLabel(
            f"جزئیات فاکتور خرید شماره PI-{self.purchase_invoice_id:04d}",
            objectName="dialogTitleLabel",
        )
        back_btn = QPushButton(
            " بازگشت به لیست", icon=QIcon(resource_path("assets/icons/arrow-right.svg"))
        )
        back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        details_frame = QFrame(objectName="formDialog")
        self.details_layout = QVBoxLayout(details_frame)
        self.details_layout.addWidget(self.title_label)

        form_layout = QFormLayout()
        self.supplier_name_label = QLabel()
        self.issue_date_label = QLabel()
        form_layout.addRow("<b>تامین‌کننده:</b>", self.supplier_name_label)
        form_layout.addRow("<b>تاریخ ثبت:</b>", self.issue_date_label)
        self.details_layout.addLayout(form_layout)
        main_layout.addWidget(details_frame)

        main_layout.addWidget(QLabel("اقلام خریداری شده:"))
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(
            ["نام کالا", "تعداد", "قیمت خرید (واحد)", "جمع"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.items_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        main_layout.addWidget(self.items_table, 1)

        bottom_frame = QFrame(objectName="formDialog")
        bottom_layout = QHBoxLayout(bottom_frame)
        self.notes_display = QTextEdit(readOnly=True)
        notes_v_layout = QVBoxLayout()
        notes_v_layout.addWidget(QLabel("<b>توضیحات فاکتور:</b>"))
        notes_v_layout.addWidget(self.notes_display)

        summary_form = QFormLayout()
        self.grand_total_label = QLabel()
        self.grand_total_label.setObjectName("statValueLabel")
        summary_form.addRow("<b>مبلغ نهایی فاکتور:</b>", self.grand_total_label)

        bottom_layout.addLayout(notes_v_layout, 1)
        bottom_layout.addLayout(summary_form, 1)
        main_layout.addWidget(bottom_frame)

        self.load_data()

    def load_data(self):
        details = self.db_manager.get_purchase_invoice_details(self.purchase_invoice_id)
        items = self.db_manager.get_purchase_invoice_items(self.purchase_invoice_id)

        if not details:
            return

        self.supplier_name_label.setText(details["supplier_name"])
        self.issue_date_label.setText(details["issue_date"])
        self.notes_display.setPlainText(details["notes"] or "توضیحاتی ثبت نشده است.")
        self.grand_total_label.setText(f"{details['total_amount']:,.0f} ریال")

        self.items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            total = item["quantity"] * item["purchase_price"]
            self.items_table.setItem(row, 0, QTableWidgetItem(item["product_name"]))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item["quantity"])))
            self.items_table.setItem(
                row, 2, QTableWidgetItem(f"{item['purchase_price']:,.0f}")
            )
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{total:,.0f}"))
