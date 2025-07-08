# file: db_updater.py
import sqlite3
import traceback
from utils import get_app_data_path

DB_NAME = get_app_data_path("accounting.db")


def add_column_if_not_exists(cursor, table_name, column_name, column_type):
    """یک ستون را به جدول اضافه می‌کند، در صورتی که از قبل وجود نداشته باشد."""
    try:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )
        print(f"ستون '{column_name}' با موفقیت به جدول '{table_name}' اضافه شد.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"ستون '{column_name}' از قبل در جدول '{table_name}' وجود دارد.")
        else:
            raise e


def run_migrations(db_path):
    print("شروع فرآیند به‌روزرسانی دیتابیس...")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\nبررسی جدول 'users'...")
        add_column_if_not_exists(cursor, "users", "secret_question", "TEXT")
        add_column_if_not_exists(cursor, "users", "secret_answer_hash", "TEXT")

        print("\nبررسی جدول 'fee_templates'...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS fee_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            value REAL NOT NULL DEFAULT 0
        );
        """
        )
        print("جدول 'fee_templates' بررسی و در صورت نیاز ایجاد شد.")
        # ---------------------------------------------------------

        print("\nبررسی جدول 'expense_categories'...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """
        )
        print("جدول 'expense_categories' بررسی و در صورت نیاز ایجاد شد.")
        # ---------------------------------------------------------

        print("\nبررسی جدول 'cheques'...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS cheques (
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
        print("جدول 'cheques' بررسی و در صورت نیاز ایجاد شد.")

        print("\nبررسی جدول 'invoices' برای اطلاعات پرداخت...")
        add_column_if_not_exists(
            cursor, "invoices", "payment_type", "TEXT DEFAULT 'نقدی'"
        )
        add_column_if_not_exists(cursor, "invoices", "payment_details", "TEXT")

        print("\nبررسی جدول 'cheques' برای اتصال به فاکتور...")
        add_column_if_not_exists(cursor, "cheques", "invoice_id", "INTEGER")

        print("\nبررسی جدول 'products' برای موجودی انبار...")
        add_column_if_not_exists(
            cursor, "products", "stock_quantity", "REAL NOT NULL DEFAULT 0"
        )

        print("\nبررسی جدول 'accounts'...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS accounts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          type TEXT NOT NULL, -- 'income' or 'expense'
          description TEXT
        );
        """
        )
        print("جدول 'accounts' بررسی و در صورت نیاز ایجاد شد.")

        print("\nبررسی جدول 'products' و 'expenses' برای افزودن account_id...")
        add_column_if_not_exists(cursor, "products", "account_id", "INTEGER")
        add_column_if_not_exists(cursor, "expenses", "account_id", "INTEGER")

        print("\nبررسی جدول 'suppliers'...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS suppliers (
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
        print("جدول 'suppliers' بررسی و در صورت نیاز ایجاد شد.")

        print("\nبررسی جداول خرید...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS purchase_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE SET NULL
        );
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS purchase_invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_invoice_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            purchase_price REAL NOT NULL,
            FOREIGN KEY (purchase_invoice_id) REFERENCES purchase_invoices (id) ON DELETE CASCADE
        );
        """
        )
        print("جداول مربوط به فاکتور خرید بررسی و در صورت نیاز ایجاد شدند.")

        print("\nبررسی جداول برای قابلیت COGS...")
        add_column_if_not_exists(
            cursor, "products", "average_purchase_price", "REAL NOT NULL DEFAULT 0"
        )
        add_column_if_not_exists(cursor, "invoice_items", "cost_of_good_sold", "REAL")

        conn.commit()

        print("\nفرآیند به‌روزرسانی دیتابیس با موفقیت پایان یافت.")

    except sqlite3.Error as e:
        print(f"خطایی در کار با SQLite رخ داد: {e}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    run_migrations()
