# file: pages/expenses_page.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QLineEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from dialogs.expense_dialog import ExpenseDialog
from dialogs.custom_message_box import CustomMessageBox
from signal_bus import signal_bus
from utils import resource_path


class ExpensesPage(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        signal_bus.expense_saved.connect(self.refresh_data)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit(
            placeholderText="جستجو بر اساس شرح یا نام حساب..."
        )
        self.search_input.textChanged.connect(self.search_expenses)
        add_btn = QPushButton(" ثبت هزینه جدید", objectName="primaryButton")
        add_btn.setIcon(QIcon(resource_path("assets/icons/dollar-sign.svg")))
        add_btn.clicked.connect(self.add_new_expense)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(add_btn)
        layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "شرح", "مبلغ (ریال)", "تاریخ", "حساب هزینه", "عملیات"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout.addWidget(self.table)
        self.load_expenses()

    def load_expenses(self, search_term=None):
        self.table.setRowCount(0)
        expenses = (
            self.db_manager.search_expenses(search_term)
            if search_term
            else self.db_manager.get_all_expenses()
        )
        self.table.setRowCount(len(expenses))
        for row, expense in enumerate(expenses):
            self.table.setItem(row, 0, QTableWidgetItem(str(expense["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(expense["description"]))
            self.table.setItem(row, 2, QTableWidgetItem(f"{expense['amount']:,.0f}"))
            self.table.setItem(row, 3, QTableWidgetItem(expense["expense_date"]))
            self.table.setItem(
                row, 4, QTableWidgetItem(expense["account_name"] or "تعیین نشده")
            )
            self.add_action_buttons(row, expense["id"])
        self.table.setColumnHidden(0, True)

    def add_action_buttons(self, row, expense_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit_btn = QPushButton(icon=QIcon(resource_path("assets/icons/edit-2.svg")), toolTip="ویرایش")
        edit_btn.clicked.connect(lambda: self.open_edit_expense_dialog(expense_id))
        delete_btn = QPushButton(icon=QIcon(resource_path("assets/icons/trash-2.svg")), toolTip="حذف")
        delete_btn.clicked.connect(lambda: self.delete_expense(expense_id))
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        self.table.setCellWidget(row, 5, widget)

    def search_expenses(self):
        self.load_expenses(self.search_input.text())

    def refresh_data(self):
        self.search_input.clear()
        self.load_expenses()

    def add_new_expense(self):
        dialog = ExpenseDialog(self.db_manager, parent=self)
        dialog.exec()

    def open_edit_expense_dialog(self, expense_id):
        dialog = ExpenseDialog(self.db_manager, expense_id=expense_id, parent=self)
        dialog.exec()

    def delete_expense(self, expense_id):
        confirm = CustomMessageBox(
            "تایید حذف", "آیا از حذف این هزینه مطمئن هستید؟", self
        )
        if confirm.exec() == QDialog.Accepted:
            success, msg = self.db_manager.delete_expense(expense_id)
            if success:
                QMessageBox.information(self, "موفق", msg)
                signal_bus.expense_saved.emit()
            else:
                QMessageBox.critical(self, "خطا", msg)
