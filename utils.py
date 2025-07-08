# file: utils.py
import sys
import os


def resource_path(relative_path):
    """
    آدرس صحیح منابع خواندنی (عکس، فونت و...) را برای حالت توسعه و فایل .exe برمی‌گرداند.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_app_data_path(file_name):
    """
    یک مسیر دائمی و چند-سکویی (cross-platform) برای ذخیره فایل‌های برنامه ایجاد می‌کند.
    - در ویندوز: از AppData استفاده می‌کند.
    - در لینوکس/مک: از پوشه home کاربر استفاده می‌کند.
    """
    # تشخیص سیستم‌عامل
    if sys.platform == "win32":
        # مسیر مخصوص ویندوز
        app_data_dir = os.path.join(os.getenv("APPDATA"), "HesabYar")
    else:
        # مسیر مخصوص لینوکس و مک
        app_data_dir = os.path.join(os.path.expanduser("~"), ".HesabYar")

    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)

    return os.path.join(app_data_dir, file_name)
