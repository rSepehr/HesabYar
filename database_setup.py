# file: database_setup.py
import sqlite3
import os
from utils import get_app_data_path

DB_NAME = get_app_data_path("accounting.db")


def create_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"شروع ساخت جداول در پایگاه داده '{db_path}'...")

        cursor.execute(
            """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            secret_question TEXT,
            secret_answer_hash TEXT
        );
        """
        )
        print("جدول 'users' با ساختار کامل ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            national_id TEXT,
            economic_code TEXT,
            postal_code TEXT
        );
        """
        )
        print("جدول 'customers' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Unpaid',
            notes TEXT,
            amount_paid REAL DEFAULT 0,
            payment_method TEXT,
            payment_date TEXT,
            cheque_number TEXT,
            cheque_due_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
        );
        """
        )
        print("جدول 'invoices' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            unit_price REAL NOT NULL,
            discount_percent REAL NOT NULL DEFAULT 0,
            tax_percent REAL NOT NULL DEFAULT 0,
            extra_costs TEXT,
            cost_of_good_sold REAL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
        );
        """
        )
        print("جدول 'invoice_items' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE purchase_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE SET NULL
        );
        """
        )
        print("جدول 'purchase_invoices' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE purchase_invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_invoice_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            purchase_price REAL NOT NULL,
            FOREIGN KEY (purchase_invoice_id) REFERENCES purchase_invoices (id) ON DELETE CASCADE
        );
        """
        )
        print("جدول 'purchase_invoice_items' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            category TEXT,
            account_id INTEGER,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        );
        """
        )
        print("جدول 'expenses' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            unit TEXT NOT NULL,
            unit_price REAL NOT NULL DEFAULT 0,
            stock_quantity REAL NOT NULL DEFAULT 0,
            account_id INTEGER,
            average_purchase_price REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        );
        """
        )
        print("جدول 'products' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE fee_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            value REAL NOT NULL DEFAULT 0
        );
        """
        )
        print("جدول 'fee_templates' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """
        )
        print("جدول 'expense_categories' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE cheques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            cheque_number TEXT NOT NULL,
            bank_name TEXT,
            amount REAL NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT
        );
        """
        )
        print("جدول 'cheques' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL, -- 'income' or 'expense'
            description TEXT
        );
        """
        )
        print("جدول 'accounts' ایجاد شد.")

        cursor.execute(
            """
        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            national_id TEXT,
            economic_code TEXT,
            postal_code TEXT
        );
        """
        )
        print("جدول 'suppliers' ایجاد شد.")

        conn.commit()
        print("تمام جداول با موفقیت و با ساختار کامل ایجاد شدند.")

    except sqlite3.Error as e:
        print(f"خطایی در کار با SQLite رخ داد: {e}")
    finally:
        if conn:
            conn.close()
            print("اتصال به پایگاه داده بسته شد.")


if __name__ == "__main__":
    create_database()
