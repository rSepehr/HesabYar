# file: pages/cheques_page.py
import jdatetime
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
)
from PySide6.QtGui import QIcon, QColor, QBrush
from PySide6.QtCore import Qt

from dialogs.cheque_dialog import ChequeDialog
from dialogs.custom_message_box import CustomMessageBox
from signal_bus import signal_bus
from utils import resource_path


class ChequesPage(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit(
            placeholderText="جستجو بر اساس شماره چک یا توضیحات..."
        )
        self.search_input.textChanged.connect(self.search_cheques)
        self.add_btn = QPushButton(" ثبت چک جدید", objectName="primaryButton")
        self.add_btn.setIcon(QIcon(resource_path("assets/icons/file-plus.svg")))
        self.add_btn.clicked.connect(self.open_add_dialog)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(self.add_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "نوع",
                "شماره چک",
                "بانک",
                "مبلغ",
                "تاریخ صدور",
                "تاریخ سررسید",
                "وضعیت",
                "فاکتور مرتبط",
                "عملیات",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            9, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.table)

        signal_bus.invoice_saved.connect(self.refresh_data)
        self.load_cheques()

    def load_cheques(self, search_term=None):
        cheques = (
            self.db_manager.search_cheques(search_term)
            if search_term
            else self.db_manager.get_all_cheques()
        )
        self.table.setRowCount(len(cheques))

        today = jdatetime.date.today()

        for row, cheque in enumerate(cheques):
            self.table.setItem(row, 0, QTableWidgetItem(str(cheque["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(cheque["type"]))
            self.table.setItem(row, 2, QTableWidgetItem(cheque["cheque_number"]))
            self.table.setItem(row, 3, QTableWidgetItem(cheque["bank_name"]))
            self.table.setItem(
                row, 4, QTableWidgetItem(f"{cheque['amount']:,.0f} ریال")
            )
            self.table.setItem(row, 5, QTableWidgetItem(cheque["issue_date"]))
            self.table.setItem(row, 6, QTableWidgetItem(cheque["due_date"]))
            self.table.setItem(row, 7, QTableWidgetItem(cheque["status"]))

            invoice_id = cheque["invoice_id"]
            invoice_text = f"INV-{invoice_id:04d}" if invoice_id else "---"
            self.table.setItem(row, 8, QTableWidgetItem(invoice_text))

            self.add_action_buttons(row, cheque["id"])

            try:
                due_date_str = cheque["due_date"].split("/")
                due_date = jdatetime.date(
                    int(due_date_str[0]), int(due_date_str[1]), int(due_date_str[2])
                )
                is_pending = cheque["status"] == "در انتظار وصول"

                if is_pending and due_date <= today:
                    color = QColor("#e74c3c")
                elif is_pending and (due_date - today).days <= 7:
                    color = QColor("#f39c12")
                elif cheque["status"] == "برگشتی":
                    color = QColor("#7f8c8d")
                else:
                    color = QColor("transparent")

                for col in range(self.table.columnCount()):
                    if self.table.item(row, col):
                        self.table.item(row, col).setBackground(color)
            except (ValueError, IndexError):
                pass

        self.table.setColumnHidden(0, True)

    def add_action_buttons(self, row, cheque_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        edit_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/edit-2.svg")), toolTip="ویرایش"
        )
        edit_btn.clicked.connect(lambda: self.open_edit_dialog(cheque_id))

        delete_btn = QPushButton(
            icon=QIcon(resource_path("assets/icons/trash-2.svg")), toolTip="حذف"
        )
        delete_btn.clicked.connect(lambda: self.delete_cheque(cheque_id))

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        self.table.setCellWidget(row, 9, widget)

    def open_add_dialog(self):
        dialog = ChequeDialog(self.db_manager, parent=self)
        dialog.exec()

    def open_edit_dialog(self, cheque_id):
        dialog = ChequeDialog(self.db_manager, cheque_id=cheque_id, parent=self)
        dialog.exec()

    def delete_cheque(self, cheque_id):
        confirm = CustomMessageBox(
            "تایید حذف",
            "آیا از حذف این چک مطمئن هستید؟\nاین عمل روی فاکتور مرتبط تاثیری ندارد.",
            self,
        )
        if confirm.exec() == QDialog.DialogCode.Accepted:
            success, msg = self.db_manager.delete_cheque(cheque_id)
            if success:
                QMessageBox.information(self, "موفق", msg)
                self.refresh_data()
            else:
                QMessageBox.critical(self, "خطا", msg)

    def search_cheques(self):
        self.load_cheques(self.search_input.text())

    def refresh_data(self):
        self.search_input.clear()
        self.load_cheques()
