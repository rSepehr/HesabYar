# file: signal_bus.py
from PySide6.QtCore import QObject, Signal


class _SignalBus(QObject):
    """
    این کلاس سیگنال‌های سراسری برنامه را نگهداری می‌کند.
    هر بخشی از برنامه می‌تواند به این سیگنال‌ها متصل شده یا آنها را ارسال کند.
    """

    customer_saved = Signal(int)
    product_saved = Signal()
    invoice_saved = Signal()
    expense_saved = Signal()
    supplier_saved = Signal()
    purchase_invoice_saved = Signal()


signal_bus = _SignalBus()
