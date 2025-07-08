# file: db_manager.py
import sqlite3
import json
import traceback
import jdatetime
from auth_utils import hash_password, check_password
from utils import get_app_data_path


class DatabaseManager:
    def __init__(self, db_name=get_app_data_path("accounting.db")):
        self.db_name = db_name

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def add_user(self, username, email, password, secret_question, secret_answer):
        """کاربر جدید را به همراه سوال و پاسخ امنیتی به دیتابیس اضافه می‌کند."""
        try:
            with self._get_connection() as conn:
                hashed_pw = hash_password(password)
                hashed_secret_answer = hash_password(secret_answer)

                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash, secret_question, secret_answer_hash) 
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (username, email, hashed_pw, secret_question, hashed_secret_answer),
                )

                new_id = cursor.lastrowid
                conn.commit()
                return True, "کاربر با موفقیت ثبت نام شد.", new_id
        except sqlite3.IntegrityError:
            return False, "نام کاربری یا ایمیل قبلاً استفاده شده است.", None
        except Exception as e:
            traceback.print_exc()
            return False, f"خطا در ثبت کاربر: {e}", None

    def check_user_credentials(self, username, password):
        """بررسی می‌کند که آیا نام کاربری و رمز عبور وارد شده صحیح است یا خیر."""
        with self._get_connection() as conn:
            result = (
                conn.cursor()
                .execute(
                    "SELECT password_hash FROM users WHERE username = ?", (username,)
                )
                .fetchone()
            )
            if result:
                is_correct = check_password(password, result["password_hash"])
                return is_correct, (
                    "اطلاعات صحیح است" if is_correct else "رمز عبور اشتباه است."
                )
            return False, "کاربری با این نام کاربری یافت نشد."

    def get_user_info(self, username):
        """اطلاعات پایه کاربر را برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute(
                    "SELECT username, email FROM users WHERE username = ?", (username,)
                )
                .fetchone()
            )

    def change_password(self, username, old_password, new_password):
        """رمز عبور کاربر را در صورت صحیح بودن رمز قدیمی، تغییر می‌دهد."""
        is_correct, _ = self.check_user_credentials(username, old_password)
        if not is_correct:
            return False, "رمز عبور فعلی اشتباه است."
        try:
            with self._get_connection() as conn:
                new_hashed_pw = hash_password(new_password)
                conn.cursor().execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (new_hashed_pw, username),
                )
                conn.commit()
                return True, "رمز عبور با موفقیت تغییر کرد."
        except Exception as e:
            return False, f"خطا در به‌روزرسانی رمز عبور: {e}"

    def get_secret_question(self, username):
        """سوال امنیتی یک کاربر را برمی‌گرداند."""
        with self._get_connection() as conn:
            result = (
                conn.cursor()
                .execute(
                    "SELECT secret_question FROM users WHERE username = ?", (username,)
                )
                .fetchone()
            )
            if result:
                return result["secret_question"]
            return None

    def check_secret_answer(self, username, secret_answer):
        """بررسی می‌کند که آیا پاسخ امنیتی وارد شده برای یک کاربر صحیح است یا خیر."""
        with self._get_connection() as conn:
            result = (
                conn.cursor()
                .execute(
                    "SELECT secret_answer_hash FROM users WHERE username = ?",
                    (username,),
                )
                .fetchone()
            )
            if result and result["secret_answer_hash"]:
                return check_password(secret_answer, result["secret_answer_hash"])
            return False

    def reset_password(self, username, new_password):
        """رمز عبور کاربر را مستقیما و بدون چک کردن رمز قدیمی، ریست می‌کند."""
        try:
            with self._get_connection() as conn:
                new_hashed_pw = hash_password(new_password)
                conn.cursor().execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (new_hashed_pw, username),
                )
                conn.commit()
                return True, "رمز عبور با موفقیت بازنشانی شد."
        except Exception as e:
            return False, f"خطا در بازنشانی رمز عبور: {e}"

    def update_security_question(self, username, question, answer):
        """سوال و جواب امنیتی کاربر را به‌روزرسانی می‌کند."""
        try:
            with self._get_connection() as conn:
                hashed_answer = hash_password(answer)
                conn.cursor().execute(
                    "UPDATE users SET secret_question = ?, secret_answer_hash = ? WHERE username = ?",
                    (question, hashed_answer, username),
                )
                conn.commit()
                return True, "سوال و جواب امنیتی با موفقیت به‌روز شد."
        except Exception as e:
            traceback.print_exc()
            return False, f"خطا در به‌روزرسانی سوال امنیتی: {e}"

    def delete_customer(self, customer_id):
        try:
            with self._get_connection() as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.cursor().execute(
                    "DELETE FROM customers WHERE id=?", (customer_id,)
                )
                conn.commit()
                return True, "مشتری با موفقیت حذف شد."
        except sqlite3.IntegrityError:
            return (
                False,
                "این مشتری دارای فاکتورهای ثبت شده است و نمی‌توان آن را حذف کرد. ابتدا فاکتورهای مربوطه را حذف کنید.",
            )
        except Exception as e:
            return False, f"خطا در حذف: {e}"

    def search_customers(self, search_term):
        with self._get_connection() as conn:
            term = f"%{search_term}%"
            return (
                conn.cursor()
                .execute(
                    "SELECT * FROM customers WHERE name LIKE ? OR national_id LIKE ?",
                    (term, term),
                )
                .fetchall()
            )

    def add_customer(
        self, name, email, phone, address, national_id, economic_code, postal_code
    ):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO customers (name, email, phone, address, national_id, economic_code, postal_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        name,
                        email,
                        phone,
                        address,
                        national_id,
                        economic_code,
                        postal_code,
                    ),
                )
                new_id = cursor.lastrowid
                conn.commit()
                return True, "مشتری با موفقیت اضافه شد.", new_id
        except Exception as e:
            traceback.print_exc()
            return False, f"خطا در افزودن مشتری: {e}", None

    def update_customer(
        self,
        customer_id,
        name,
        email,
        phone,
        address,
        national_id,
        economic_code,
        postal_code,
    ):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE customers SET name=?, email=?, phone=?, address=?, national_id=?, economic_code=?, postal_code=? WHERE id=?",
                    (
                        name,
                        email,
                        phone,
                        address,
                        national_id,
                        economic_code,
                        postal_code,
                        customer_id,
                    ),
                )
                conn.commit()
                return True, "اطلاعات مشتری با موفقیت به‌روز شد."
        except Exception as e:
            traceback.print_exc()
            return False, f"خطا در به‌روزرسانی: {e}"

    def get_customer_by_id(self, customer_id):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM customers WHERE id=?", (customer_id,))
                .fetchone()
            )

    def get_all_customers(self):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM customers ORDER BY name")
                .fetchall()
            )

    def check_for_duplicates(self, name, email, phone, customer_id=None):
        with self._get_connection() as conn:
            where_clauses, params = [], []
            if name:
                where_clauses.append("LOWER(name) = ?")
                params.append(name.lower())
            if email:
                where_clauses.append("email = ?")
                params.append(email)
            if phone:
                where_clauses.append("phone = ?")
                params.append(phone)
            if not where_clauses:
                return []
            query = f"SELECT name, email, phone FROM customers WHERE ({' OR '.join(where_clauses)})"
            if customer_id:
                query += " AND id != ?"
                params.append(customer_id)
            return conn.cursor().execute(query, tuple(params)).fetchall()

    def search_products(self, search_term):
        with self._get_connection() as conn:
            term = f"%{search_term}%"
            return (
                conn.cursor()
                .execute(
                    "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?",
                    (term, term),
                )
                .fetchall()
            )

    def add_product(
        self, name, description, unit, unit_price, stock_quantity, account_id
    ):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "INSERT INTO products (name, description, unit, unit_price, stock_quantity, account_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, description, unit, unit_price, stock_quantity, account_id),
                )
                conn.commit()
                return True, "کالا با موفقیت اضافه شد."
        except sqlite3.IntegrityError:
            return False, "کالایی با این نام از قبل وجود دارد."
        except Exception as e:
            return False, f"خطا در افزودن کالا: {e}"

    def update_product(
        self,
        product_id,
        name,
        description,
        unit,
        unit_price,
        stock_quantity,
        account_id,
    ):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE products SET name=?, description=?, unit=?, unit_price=?, stock_quantity=?, account_id=? WHERE id=?",
                    (
                        name,
                        description,
                        unit,
                        unit_price,
                        stock_quantity,
                        account_id,
                        product_id,
                    ),
                )
                conn.commit()
                return True, "کالا با موفقیت به‌روز شد."
        except sqlite3.IntegrityError:
            return False, "کالایی دیگر با همین نام وجود دارد."
        except Exception as e:
            return False, f"خطا در به‌روزرسانی: {e}"

    def decrease_product_stock(self, product_id, quantity_sold):
        """موجودی یک کالا را پس از فروش کاهش می‌دهد."""
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                    (quantity_sold, product_id),
                )
                conn.commit()
                return True, ""
        except Exception as e:
            return False, f"خطا در کاهش موجودی کالا ID {product_id}: {e}"

    def get_product_by_id(self, product_id):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM products WHERE id=?", (product_id,))
                .fetchone()
            )

    def get_all_products(self):
        with self._get_connection() as conn:
            return (
                conn.cursor().execute("SELECT * FROM products ORDER BY name").fetchall()
            )

    def get_distinct_units(self):
        with self._get_connection() as conn:
            return [
                item["unit"]
                for item in conn.cursor()
                .execute(
                    "SELECT DISTINCT unit FROM products WHERE unit IS NOT NULL AND unit != '' ORDER BY unit"
                )
                .fetchall()
            ]

    def delete_product(self, product_id):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute("DELETE FROM products WHERE id=?", (product_id,))
                conn.commit()
                return True, "کالا با موفقیت حذف شد."
        except Exception as e:
            return False, f"خطا در حذف: {e}"

    def get_fee_templates(self):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM fee_templates ORDER BY name")
                .fetchall()
            )

    def add_fee_template(self, name, fee_type, value):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "INSERT INTO fee_templates (name, type, value) VALUES (?, ?, ?)",
                    (name, fee_type, value),
                )
                conn.commit()
                return True, "قالب هزینه با موفقیت اضافه شد."
        except sqlite3.IntegrityError:
            return False, "قالب هزینه‌ای با این نام از قبل وجود دارد."
        except Exception as e:
            return False, f"خطا در افزودن قالب هزینه: {e}"

    def update_fee_template(self, fee_id, name, fee_type, value):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE fee_templates SET name=?, type=?, value=? WHERE id=?",
                    (name, fee_type, value, fee_id),
                )
                conn.commit()
                return True, "قالب هزینه با موفقیت به‌روز شد."
        except sqlite3.IntegrityError:
            return False, "قالب هزینه‌ای دیگر با این نام وجود دارد."
        except Exception as e:
            return False, f"خطا در به‌روزرسانی قالب هزینه: {e}"

    def delete_fee_template(self, fee_id):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute("DELETE FROM fee_templates WHERE id=?", (fee_id,))
                conn.commit()
                return True, "قالب هزینه با موفقیت حذف شد."
        except Exception as e:
            return False, f"خطا در حذف قالب هزینه: {e}"

    def get_fee_template_by_id(self, fee_id):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM fee_templates WHERE id=?", (fee_id,))
                .fetchone()
            )

    def get_all_expense_categories(self):
        """تمام دسته‌بندی‌های هزینه را برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM expense_categories ORDER BY name")
                .fetchall()
            )

    def update_expense_category(self, category_id, name):
        """یک دسته‌بندی هزینه را به‌روزرسانی می‌کند."""
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE expense_categories SET name=? WHERE id=?",
                    (name, category_id),
                )
                conn.commit()
                return True, "دسته‌بندی با موفقیت به‌روز شد."
        except sqlite3.IntegrityError:
            return False, "دسته‌بندی دیگری با این نام وجود دارد."
        except Exception as e:
            return False, f"خطا در به‌روزرسانی: {e}"

    def delete_expense_category(self, category_id):
        """یک دسته‌بندی هزینه را حذف می‌کند."""
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "DELETE FROM expense_categories WHERE id=?", (category_id,)
                )
                conn.commit()
                return True, "دسته‌بندی با موفقیت حذف شد."
        except Exception as e:
            return False, f"خطا در حذف دسته‌بندی: {e}"

    def get_expense_category_by_id(self, category_id):
        """یک دسته‌بندی را با ID آن برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM expense_categories WHERE id=?", (category_id,))
                .fetchone()
            )

    def search_invoices(self, search_term):
        """Searches invoices by customer name or invoice ID."""
        with self._get_connection() as conn:
            term = f"%{search_term}%"
            id_term = search_term.replace("INV-", "").strip()

            query = """
            SELECT inv.*, cust.name as customer_name
            FROM invoices inv
            JOIN customers cust ON inv.customer_id = cust.id
            WHERE cust.name LIKE ? OR inv.id LIKE ?
            ORDER BY inv.issue_date DESC
            """
            return conn.cursor().execute(query, (term, f"%{id_term}%")).fetchall()

    def save_invoice(self, invoice_data, items_data):
        """فاکتور فروش، اقلام و هزینه تمام شده هر قلم را ذخیره می‌کند."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")

            sql = """INSERT INTO invoices (
                         customer_id, issue_date, total_amount, status, notes, 
                         amount_paid, payment_method, payment_date, cheque_number, cheque_due_date
                     ) VALUES (
                         :customer_id, :issue_date, :total_amount, :status, :notes, 
                         :amount_paid, :payment_method, :payment_date, :cheque_number, :cheque_due_date
                     )"""
            cursor.execute(sql, invoice_data)
            invoice_id = cursor.lastrowid

            for item in items_data:
                extra_costs_json = json.dumps(
                    item.get("extra_costs", []), ensure_ascii=False
                )
                cursor.execute(
                    """INSERT INTO invoice_items (invoice_id, description, quantity, unit, 
                                                  unit_price, discount_percent, tax_percent, 
                                                  extra_costs, cost_of_good_sold)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        invoice_id,
                        item["description"],
                        item["quantity"],
                        item["unit"],
                        item["unit_price"],
                        item["discount_percent"],
                        item["tax_percent"],
                        extra_costs_json,
                        item["cost_of_good_sold"],
                    ),
                )

            conn.commit()
            return True, f"فاکتور با شماره {invoice_id} با موفقیت صادر شد.", invoice_id
        except Exception as e:
            conn.rollback()
            traceback.print_exc()
            return False, f"خطا در صدور فاکتور: {e}", None
        finally:
            if conn:
                conn.close()

    def get_all_invoices(self):
        """
        تمام فاکتورها را برمی‌گرداند و بر اساس وضعیت (پرداخت نشده > کسری > پرداخت شده) مرتب می‌کند.
        """
        with self._get_connection() as conn:
            query = """
                SELECT inv.*, cust.name as customer_name 
                FROM invoices inv 
                JOIN customers cust ON inv.customer_id = cust.id 
                ORDER BY 
                    CASE inv.status 
                        WHEN 'پرداخت نشده' THEN 1 
                        WHEN 'کسری' THEN 2 
                        WHEN 'پرداخت شده' THEN 3 
                        ELSE 4 
                    END, 
                    inv.issue_date DESC
            """
            return conn.cursor().execute(query).fetchall()

    def get_invoices_for_customer(self, customer_id):
        """تمام فاکتورهای مربوط به یک مشتری خاص را برمی‌گرداند."""
        with self._get_connection() as conn:
            query = """
                SELECT inv.*, cust.name as customer_name 
                FROM invoices inv 
                JOIN customers cust ON inv.customer_id = cust.id 
                WHERE inv.customer_id = ? 
                ORDER BY inv.issue_date DESC
            """
            return conn.cursor().execute(query, (customer_id,)).fetchall()

    def get_invoice_details(self, invoice_id):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute(
                    "SELECT inv.*, cust.name as customer_name, cust.national_id, cust.economic_code, cust.phone, cust.address, cust.postal_code FROM invoices inv JOIN customers cust ON inv.customer_id = cust.id WHERE inv.id = ?",
                    (invoice_id,),
                )
                .fetchone()
            )

    def get_invoice_items(self, invoice_id):
        with self._get_connection() as conn:
            items = []
            for row in (
                conn.cursor()
                .execute(
                    "SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)
                )
                .fetchall()
            ):
                item_dict = dict(row)
                try:
                    item_dict["extra_costs"] = (
                        json.loads(row["extra_costs"]) if row["extra_costs"] else []
                    )
                except (json.JSONDecodeError, TypeError):
                    item_dict["extra_costs"] = []
                items.append(item_dict)
            return items

    def get_all_invoice_items(self):
        with self._get_connection() as conn:
            return [
                dict(row)
                for row in conn.cursor()
                .execute("SELECT * FROM invoice_items ORDER BY invoice_id")
                .fetchall()
            ]

    def delete_invoice(self, invoice_id):
        """یک فاکتور و تمام اقلام و چک‌های مرتبط با آن را حذف می‌کند."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")

                cursor.execute("DELETE FROM cheques WHERE invoice_id=?", (invoice_id,))

                cursor.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))

                conn.commit()
                return True, "فاکتور و اطلاعات مرتبط (چک) با موفقیت حذف شدند."
        except Exception as e:
            import traceback

            traceback.print_exc()
            return False, f"خطا در حذف فاکتور: {e}"

    def add_payment(self, invoice_id, new_payment_amount):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT total_amount, amount_paid FROM invoices WHERE id=?",
                    (invoice_id,),
                )
                result = cursor.fetchone()
                if not result:
                    return False, "فاکتوری با این شناسه یافت نشد."

                total_amount = result["total_amount"]
                current_amount_paid = result["amount_paid"] or 0
                new_total_paid = current_amount_paid + new_payment_amount

                if new_total_paid >= total_amount:
                    new_status = "پرداخت شده"
                    new_total_paid = total_amount
                elif new_total_paid > 0:
                    new_status = "کسری"
                else:
                    new_status = "پرداخت نشده"

                cursor.execute(
                    "UPDATE invoices SET amount_paid=?, status=? WHERE id=?",
                    (new_total_paid, new_status, invoice_id),
                )
                conn.commit()
                return True, "پرداخت با موفقیت ثبت شد."
        except Exception as e:
            traceback.print_exc()
            return False, f"خطا در ثبت پرداخت: {e}"

    def search_expenses(self, search_term):
        with self._get_connection() as conn:
            term = f"%{search_term}%"
            query = """
                SELECT exp.*, acc.name as account_name 
                FROM expenses exp
                LEFT JOIN accounts acc ON exp.account_id = acc.id
                WHERE exp.description LIKE ? OR acc.name LIKE ?
                ORDER BY exp.expense_date DESC
            """
            return conn.cursor().execute(query, (term, term)).fetchall()

    def add_expense(self, description, amount, expense_date, category, account_id):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "INSERT INTO expenses (description, amount, expense_date, category, account_id) VALUES (?, ?, ?, ?, ?)",
                    (description, amount, expense_date, category, account_id),
                )
                conn.commit()
                return True, "هزینه با موفقیت ثبت شد."
        except Exception as e:
            return False, f"خطا در ثبت هزینه: {e}"

    def get_all_expenses(self):
        with self._get_connection() as conn:
            query = """
                SELECT exp.*, acc.name as account_name 
                FROM expenses exp
                LEFT JOIN accounts acc ON exp.account_id = acc.id
                ORDER BY exp.expense_date DESC
            """
            return conn.cursor().execute(query).fetchall()

    def delete_expense(self, expense_id):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute("DELETE FROM expenses WHERE id=?", (expense_id,))
                conn.commit()
                return True, "هزینه با موفقیت حذف شد."
        except Exception as e:
            return False, f"خطا در حذف هزینه: {e}"

    def get_expense_by_id(self, expense_id):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM expenses WHERE id=?", (expense_id,))
                .fetchone()
            )

    def update_expense(
        self, expense_id, description, amount, expense_date, category, account_id
    ):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE expenses SET description=?, amount=?, expense_date=?, category=?, account_id=? WHERE id=?",
                    (
                        description,
                        amount,
                        expense_date,
                        category,
                        account_id,
                        expense_id,
                    ),
                )
                conn.commit()
                return True, "هزینه با موفقیت به‌روز شد."
        except Exception as e:
            return False, f"خطا در به‌روزرسانی هزینه: {e}"

    # --- متدهای گزارش‌گیری (Reporting & Other Methods) ---
    def get_stats_for_dashboard(self):
        with self._get_connection() as conn:
            c = conn.cursor()
            today_str = jdatetime.date.today().strftime("%Y/%m/%d")
            c.execute(
                "SELECT SUM(total_amount) FROM invoices WHERE issue_date = ?",
                (today_str,),
            )
            sales_today = c.fetchone()[0] or 0
            month_str_like = jdatetime.date.today().strftime("%Y/%m") + "%"
            c.execute(
                "SELECT SUM(total_amount) FROM invoices WHERE issue_date LIKE ?",
                (month_str_like,),
            )
            sales_month = c.fetchone()[0] or 0
            c.execute(
                "SELECT SUM(total_amount - amount_paid) FROM invoices WHERE status IN ('Unpaid', 'Partially Paid')"
            )
            total_receivables = c.fetchone()[0] or 0
            return {
                "sales_today": sales_today,
                "sales_month": sales_month,
                "total_receivables": total_receivables,
            }

    def get_dashboard_kpis(self):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(id) FROM invoices")
            invoice_count = c.fetchone()[0] or 0
            c.execute("SELECT AVG(total_amount) FROM invoices")
            avg_invoice_amount = c.fetchone()[0] or 0
            return {
                "invoice_count": invoice_count,
                "avg_invoice_amount": avg_invoice_amount,
            }

    def get_financial_summary(self):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT SUM(amount_paid) FROM invoices")
            total_income = c.fetchone()[0] or 0
            c.execute(
                "SELECT SUM(total_amount - amount_paid) FROM invoices WHERE status IN ('Unpaid', 'Partially Paid')"
            )
            total_receivables = c.fetchone()[0] or 0
            c.execute("SELECT SUM(amount) FROM expenses")
            total_expenses = c.fetchone()[0] or 0
            return {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "total_receivables": total_receivables,
            }

    def get_recent_open_invoices(self, limit=5):
        """آخرین N فاکتور پرداخت نشده یا دارای کسری را برمی‌گرداند."""
        with self._get_connection() as conn:
            query = """
                SELECT id, issue_date, total_amount, customer_id
                FROM invoices 
                WHERE status IN ('Unpaid', 'Partially Paid')
                ORDER BY issue_date DESC
                LIMIT ?
            """
            invoices = conn.cursor().execute(query, (limit,)).fetchall()

            results = []
            for inv in invoices:
                customer_name = (
                    conn.cursor()
                    .execute(
                        "SELECT name FROM customers WHERE id = ?", (inv["customer_id"],)
                    )
                    .fetchone()
                )
                results.append(
                    {
                        "id": inv["id"],
                        "customer_name": (
                            customer_name[0] if customer_name else "حذف شده"
                        ),
                        "issue_date": inv["issue_date"],
                        "total_amount": inv["total_amount"],
                    }
                )
            return results

    def get_sales_last_n_days(self, days=7):
        """مجموع فروش هر روز را برای N روز گذشته برمی‌گرداند."""
        sales_data = {}
        today = jdatetime.date.today()
        with self._get_connection() as conn:
            c = conn.cursor()
            for i in range(days):
                day = today - jdatetime.timedelta(days=i)
                day_str = day.strftime("%Y/%m/%d")
                c.execute(
                    "SELECT SUM(total_amount) FROM invoices WHERE issue_date = ?",
                    (day_str,),
                )
                result = c.fetchone()[0]
                sales_data[day_str] = result or 0
        return dict(sorted(sales_data.items()))

    def get_expenses_by_category(self):
        """مجموع هزینه‌ها را به تفکیک دسته‌بندی برمی‌گرداند."""
        with self._get_connection() as conn:
            query = "SELECT category, SUM(amount) as total FROM expenses WHERE category IS NOT NULL AND category != '' GROUP BY category"
            results = conn.cursor().execute(query).fetchall()
            return {row["category"]: row["total"] for row in results}

    def get_extended_kpis(self):
        """KPI های بیشتری را برای داشبورد برمی‌گرداند."""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(id) FROM customers")
            customer_count = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(id) FROM products")
            product_count = c.fetchone()[0] or 0

            c.execute(
                "SELECT COUNT(id) FROM invoices WHERE status IN ('Unpaid', 'Partially Paid')"
            )
            open_invoices_count = c.fetchone()[0] or 0

            return {
                "customer_count": customer_count,
                "product_count": product_count,
                "open_invoices_count": open_invoices_count,
            }

    def get_financial_summary_by_date_range(self, start_date, end_date):
        """
        درآمد، هزینه و سود خالص را برای یک بازه زمانی مشخص محاسبه می‌کند.
        - درآمد: مجموع کل فاکتورهای صادر شده در بازه زمانی (مبنای تعهدی).
        - هزینه: مجموع کل هزینه‌های ثبت شده در بازه زمانی.
        """
        with self._get_connection() as conn:
            c = conn.cursor()

            c.execute(
                "SELECT SUM(total_amount) FROM invoices WHERE issue_date BETWEEN ? AND ?",
                (start_date, end_date),
            )
            total_revenue = c.fetchone()[0] or 0

            c.execute(
                "SELECT SUM(amount) FROM expenses WHERE expense_date BETWEEN ? AND ?",
                (start_date, end_date),
            )
            total_expenses = c.fetchone()[0] or 0

            net_profit = total_revenue - total_expenses

            return {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
            }

    def add_cheque(self, data):
        """یک چک جدید به همراه آیدی فاکتور متصل به آن، به دیتابیس اضافه می‌کند."""
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    """
                    INSERT INTO cheques (type, cheque_number, bank_name, amount, issue_date, 
                                         due_date, status, description, invoice_id)
                    VALUES (:type, :cheque_number, :bank_name, :amount, :issue_date, 
                            :due_date, :status, :description, :invoice_id)
                """,
                    data,
                )

                conn.commit()
                return True, "چک با موفقیت ثبت شد."
        except Exception as e:
            import traceback

            traceback.print_exc()
            return False, f"خطا در ثبت چک: {e}"

    def update_cheque(self, cheque_id, data):
        """اطلاعات یک چک را به‌روزرسانی می‌کند."""
        try:
            with self._get_connection() as conn:
                data["id"] = cheque_id
                conn.cursor().execute(
                    """
                    UPDATE cheques SET 
                        type = :type, 
                        cheque_number = :cheque_number, 
                        bank_name = :bank_name, 
                        amount = :amount, 
                        issue_date = :issue_date, 
                        due_date = :due_date, 
                        status = :status, 
                        description = :description
                    WHERE id = :id
                """,
                    data,
                )
                conn.commit()
                return True, "اطلاعات چک با موفقیت به‌روز شد."
        except Exception as e:
            traceback.print_exc()
            return False, f"خطا در به‌روزرسانی چک: {e}"

    def get_all_cheques(self):
        """تمام چک‌ها را بر اساس تاریخ سررسید مرتب کرده و برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM cheques ORDER BY due_date")
                .fetchall()
            )

    def get_cheque_by_id(self, cheque_id):
        """اطلاعات یک چک را با ID آن برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM cheques WHERE id = ?", (cheque_id,))
                .fetchone()
            )

    def delete_cheque(self, cheque_id):
        """یک چک را از دیتابیس حذف می‌کند."""
        try:
            with self._get_connection() as conn:
                conn.cursor().execute("DELETE FROM cheques WHERE id = ?", (cheque_id,))
                conn.commit()
                return True, "چک با موفقیت حذف شد."
        except Exception as e:
            return False, f"خطا در حذف چک: {e}"

    def search_cheques(self, search_term):
        """چک‌ها را بر اساس شماره چک یا توضیحات جستجو می‌کند."""
        with self._get_connection() as conn:
            term = f"%{search_term}%"
            return (
                conn.cursor()
                .execute(
                    "SELECT * FROM cheques WHERE cheque_number LIKE ? OR description LIKE ? ORDER BY due_date",
                    (term, term),
                )
                .fetchall()
            )

    def get_general_journal(self, start_date, end_date):
        """
        تمام تراکنش‌ها (فروش و هزینه) را در یک بازه زمانی مشخص استخراج کرده
        و به صورت یک لیست واحد و مرتب شده بر اساس تاریخ برمی‌گرداند.
        """
        transactions = []
        with self._get_connection() as conn:
            invoices = (
                conn.cursor()
                .execute(
                    "SELECT id, issue_date, total_amount FROM invoices WHERE issue_date BETWEEN ? AND ?",
                    (start_date, end_date),
                )
                .fetchall()
            )
            for inv in invoices:
                transactions.append(
                    {
                        "date": inv["issue_date"],
                        "type": "درآمد",
                        "description": f"فروش طبق فاکتور شماره {inv['id']}",
                        "income": inv["total_amount"],
                        "expense": 0,
                    }
                )

            expenses = (
                conn.cursor()
                .execute(
                    "SELECT expense_date, description, amount FROM expenses WHERE expense_date BETWEEN ? AND ?",
                    (start_date, end_date),
                )
                .fetchall()
            )
            for exp in expenses:
                transactions.append(
                    {
                        "date": exp["expense_date"],
                        "type": "هزینه",
                        "description": exp["description"],
                        "income": 0,
                        "expense": exp["amount"],
                    }
                )

        transactions.sort(key=lambda x: x["date"])
        return transactions

    def get_low_stock_products(self, threshold=10):
        """Returns products with stock quantity less than or equal to a threshold."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute(
                    "SELECT name, stock_quantity FROM products WHERE stock_quantity <= ? AND stock_quantity > 0 ORDER BY stock_quantity",
                    (threshold,),
                )
                .fetchall()
            )

    def get_upcoming_cheques(self, limit=5):
        """آخرین چک‌های دریافتی که در انتظار وصول هستند را برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute(
                    "SELECT cheque_number, due_date, amount FROM cheques WHERE type='دریافتی' AND status='در انتظار وصول' ORDER BY due_date ASC LIMIT ?",
                    (limit,),
                )
                .fetchall()
            )

    def add_account(self, name, acc_type, description):
        """یک حساب جدید اضافه می‌کند."""
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "INSERT INTO accounts (name, type, description) VALUES (?, ?, ?)",
                    (name, acc_type, description),
                )
                conn.commit()
                return True, "حساب با موفقیت اضافه شد."
        except sqlite3.IntegrityError:
            return False, "حسابی با این نام از قبل وجود دارد."
        except Exception as e:
            return False, f"خطا در افزودن حساب: {e}"

    def get_all_accounts(self):
        """تمام حساب‌ها را بر اساس نوع و نام برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM accounts ORDER BY type, name")
                .fetchall()
            )

    def get_accounts_by_type(self, acc_type):
        """تمام حساب‌های یک نوع خاص (income یا expense) را برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute(
                    "SELECT * FROM accounts WHERE type = ? ORDER BY name", (acc_type,)
                )
                .fetchall()
            )

    def update_account(self, account_id, name, acc_type, description):
        """یک حساب را به‌روزرسانی می‌کند."""
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE accounts SET name=?, type=?, description=? WHERE id=?",
                    (name, acc_type, description, account_id),
                )
                conn.commit()
                return True, "حساب با موفقیت به‌روز شد."
        except sqlite3.IntegrityError:
            return False, "حساب دیگری با این نام وجود دارد."
        except Exception as e:
            return False, f"خطا در به‌روزرسانی: {e}"

    def delete_account(self, account_id):
        """یک حساب را حذف می‌کند."""
        try:
            with self._get_connection() as conn:
                conn.cursor().execute("DELETE FROM accounts WHERE id=?", (account_id,))
                conn.commit()
                return True, "حساب با موفقیت حذف شد."
        except Exception as e:
            return False, f"خطا در حذف حساب: {e}"

    def get_account_by_id(self, account_id):
        """اطلاعات یک حساب را با ID آن برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
                .fetchone()
            )

    def add_supplier(
        self, name, email, phone, address, national_id, economic_code, postal_code
    ):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO suppliers (name, email, phone, address, national_id, economic_code, postal_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        name,
                        email,
                        phone,
                        address,
                        national_id,
                        economic_code,
                        postal_code,
                    ),
                )
                new_id = cursor.lastrowid
                conn.commit()
                return True, "تامین‌کننده با موفقیت اضافه شد.", new_id
        except Exception as e:
            return False, f"خطا در افزودن تامین‌کننده: {e}", None

    def update_supplier(
        self,
        supplier_id,
        name,
        email,
        phone,
        address,
        national_id,
        economic_code,
        postal_code,
    ):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE suppliers SET name=?, email=?, phone=?, address=?, national_id=?, economic_code=?, postal_code=? WHERE id=?",
                    (
                        name,
                        email,
                        phone,
                        address,
                        national_id,
                        economic_code,
                        postal_code,
                        supplier_id,
                    ),
                )
                conn.commit()
                return True, "اطلاعات تامین‌کننده با موفقیت به‌روز شد."
        except Exception as e:
            return False, f"خطا در به‌روزرسانی: {e}"

    def get_all_suppliers(self):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM suppliers ORDER BY name")
                .fetchall()
            )

    def get_supplier_by_id(self, supplier_id):
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,))
                .fetchone()
            )

    def delete_supplier(self, supplier_id):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "DELETE FROM suppliers WHERE id=?", (supplier_id,)
                )
                conn.commit()
                return True, "تامین‌کننده با موفقیت حذف شد."
        except Exception as e:
            return False, f"خطا در حذف: {e}"

    def save_purchase_invoice(self, invoice_data, items_data):
        """یک فاکتور خرید و اقلام آن را در دیتابیس ذخیره می‌کند."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")

            sql = """INSERT INTO purchase_invoices (supplier_id, issue_date, total_amount, notes)
                     VALUES (:supplier_id, :issue_date, :total_amount, :notes)"""
            cursor.execute(sql, invoice_data)
            purchase_invoice_id = cursor.lastrowid

            for item in items_data:
                cursor.execute(
                    """INSERT INTO purchase_invoice_items (purchase_invoice_id, product_name, quantity, purchase_price)
                       VALUES (?, ?, ?, ?)""",
                    (
                        purchase_invoice_id,
                        item["product_name"],
                        item["quantity"],
                        item["purchase_price"],
                    ),
                )

            conn.commit()
            return (
                True,
                f"فاکتور خرید با شماره {purchase_invoice_id} با موفقیت ثبت شد.",
                purchase_invoice_id,
            )
        except Exception as e:
            conn.rollback()
            traceback.print_exc()
            return False, f"خطا در ثبت فاکتور خرید: {e}", None
        finally:
            if conn:
                conn.close()

    def get_all_purchase_invoices(self):
        """تمام فاکتورهای خرید را به همراه نام تامین‌کننده برمی‌گرداند."""
        with self._get_connection() as conn:
            query = """
                SELECT pi.*, s.name as supplier_name 
                FROM purchase_invoices pi
                LEFT JOIN suppliers s ON pi.supplier_id = s.id
                ORDER BY pi.issue_date DESC
            """
            return conn.cursor().execute(query).fetchall()

    def delete_purchase_invoice(self, purchase_invoice_id):
        """یک فاکتور خرید را حذف می‌کند (اقلام آن نیز خودکار حذف می‌شوند)."""
        try:
            with self._get_connection() as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.cursor().execute(
                    "DELETE FROM purchase_invoices WHERE id=?", (purchase_invoice_id,)
                )
                conn.commit()
                return True, "فاکتور خرید با موفقیت حذف شد."
        except Exception as e:
            return False, f"خطا در حذف فاکتور خرید: {e}"

    def update_product_after_purchase(
        self, product_id, quantity_purchased, purchase_price
    ):
        """
        موجودی انبار را افزایش داده و میانگین قیمت خرید کالا را مجددا محاسبه می‌کند.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                current_data = cursor.execute(
                    "SELECT stock_quantity, average_purchase_price FROM products WHERE id = ?",
                    (product_id,),
                ).fetchone()

                if not current_data:
                    return False, f"کالایی با شناسه {product_id} یافت نشد."

                old_stock = current_data["stock_quantity"] or 0
                old_avg_price = current_data["average_purchase_price"] or 0

                total_old_value = old_stock * old_avg_price
                total_new_value = quantity_purchased * purchase_price
                new_total_stock = old_stock + quantity_purchased

                new_avg_price = (
                    (total_old_value + total_new_value) / new_total_stock
                    if new_total_stock > 0
                    else 0
                )

                cursor.execute(
                    "UPDATE products SET stock_quantity = ?, average_purchase_price = ? WHERE id = ?",
                    (new_total_stock, new_avg_price, product_id),
                )
                conn.commit()
                return True, ""
        except Exception as e:
            traceback.print_exc()
            return False, f"خطا در آپدیت کالا پس از خرید: {e}"

    def get_purchase_invoice_details(self, purchase_invoice_id):
        """اطلاعات کلی یک فاکتور خرید را به همراه نام تامین‌کننده برمی‌گرداند."""
        with self._get_connection() as conn:
            query = """
                SELECT pi.*, s.name as supplier_name 
                FROM purchase_invoices pi
                LEFT JOIN suppliers s ON pi.supplier_id = s.id
                WHERE pi.id = ?
            """
            return conn.cursor().execute(query, (purchase_invoice_id,)).fetchone()

    def get_purchase_invoice_items(self, purchase_invoice_id):
        """تمام اقلام یک فاکتور خرید مشخص را برمی‌گرداند."""
        with self._get_connection() as conn:
            return (
                conn.cursor()
                .execute(
                    "SELECT * FROM purchase_invoice_items WHERE purchase_invoice_id = ?",
                    (purchase_invoice_id,),
                )
                .fetchall()
            )

    def get_detailed_financial_summary(self, start_date, end_date):
        """
        Returns the final, detailed financial report including gross and net profit.
        """
        summary = {
            "total_revenue": 0,
            "cogs": 0,
            "gross_profit": 0,
            "total_operational_expenses": 0,
            "net_profit": 0,
            "revenue_by_account": [],
            "expenses_by_account": [],
        }
        with self._get_connection() as conn:
            cursor = conn.cursor()

            rev_query = """
                SELECT acc.name as account_name, SUM(ii.quantity * ii.unit_price) as total
                FROM invoices inv
                JOIN invoice_items ii ON inv.id = ii.invoice_id
                JOIN products p ON ii.description = p.name
                JOIN accounts acc ON p.account_id = acc.id
                WHERE inv.issue_date BETWEEN ? AND ?
                GROUP BY acc.name
            """
            summary["revenue_by_account"] = cursor.execute(
                rev_query, (start_date, end_date)
            ).fetchall()
            summary["total_revenue"] = sum(
                item["total"] for item in summary["revenue_by_account"]
            )

            cogs_query = """
                SELECT SUM(ii.cost_of_good_sold) as total_cogs
                FROM invoices inv
                JOIN invoice_items ii ON inv.id = ii.invoice_id
                WHERE inv.issue_date BETWEEN ? AND ?
            """
            cogs_result = cursor.execute(cogs_query, (start_date, end_date)).fetchone()
            summary["cogs"] = (
                cogs_result["total_cogs"]
                if cogs_result and cogs_result["total_cogs"] is not None
                else 0
            )

            exp_query = """
                SELECT acc.name as account_name, SUM(exp.amount) as total
                FROM expenses exp
                JOIN accounts acc ON exp.account_id = acc.id
                WHERE exp.expense_date BETWEEN ? AND ?
                GROUP BY acc.name
            """
            summary["expenses_by_account"] = cursor.execute(
                exp_query, (start_date, end_date)
            ).fetchall()
            summary["total_operational_expenses"] = sum(
                item["total"] for item in summary["expenses_by_account"]
            )

            # 4. Calculate final values
            summary["gross_profit"] = summary["total_revenue"] - summary["cogs"]
            total_expenses = summary["cogs"] + summary["total_operational_expenses"]
            summary["net_profit"] = summary["total_revenue"] - total_expenses

            return summary
