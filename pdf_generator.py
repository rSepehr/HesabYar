# file: pdf_generator.py
import os
import datetime
import traceback
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageTemplate,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from num2words import num2words
from bidi.algorithm import get_display
from pathlib import Path
from utils import resource_path


def rtl(text):
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)


def rp(text):
    reshaped_text = arabic_reshaper.reshape(str(text))
    bidi_text = get_display(reshaped_text)
    return bidi_text


def setup_fonts():
    if "Vazir" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont("Vazir", resource_path("assets/fonts/Vazirmatn-Regular.ttf"))
        )
    if "Vazir-Bold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont("Vazir-Bold", resource_path("assets/fonts/Vazirmatn-Bold.ttf"))
        )


def to_persian_digits(text):
    return str(text or "").translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def rp(text):
    return get_display(arabic_reshaper.reshape(str(text)))
    return text


def P(text, style):
    return Paragraph(text, style)


def num_to_words_persian(number):
    try:
        words = num2words(int(number), lang="fa")
        words = rp(words)
        return f"{rp('ریال')} {words}"
    except (ValueError, TypeError):
        return rp("صفر ریال")


class InvoiceDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(
            self.leftMargin, self.bottomMargin, self.width, self.height, id="normal"
        )
        template = PageTemplate(id="main", frames=[frame], onPage=self.draw_page_number)
        self.addPageTemplates([template])

    def draw_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Vazir", 9)
        canvas.drawCentredString(
            doc.pagesize[0] / 2, 10 * mm, rp(f"صفحه {to_persian_digits(doc.page)}")
        )
        canvas.restoreState()


def generate_invoice_pdf(invoice_details, items_data, company_info, page_size_str="A4"):
    setup_fonts()
    output_folder = Path.home() / "Documents" / "HesabYar_Invoices"
    output_folder.mkdir(parents=True, exist_ok=True)

    file_path = os.path.join(
        output_folder,
        f"invoice_{invoice_details.get('id', 'NA')}_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf",
    )

    page_size = A5 if page_size_str == "A5" else A4
    doc = InvoiceDocTemplate(
        file_path,
        pagesize=page_size,
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=20 * mm,
    )

    style_right_bold = ParagraphStyle(
        name="right_bold", fontName="Vazir-Bold", fontSize=8.5, alignment=2
    )
    style_right_normal = ParagraphStyle(
        name="right_normal", fontName="Vazir", fontSize=8.5, alignment=2, leading=12
    )
    style_left_normal = ParagraphStyle(
        name="left_normal", fontName="Vazir", fontSize=8.5, alignment=0, leading=12
    )
    style_center_bold = ParagraphStyle(
        name="center_bold", fontName="Vazir-Bold", fontSize=8, alignment=1
    )
    style_center_normal = ParagraphStyle(
        name="center_normal", fontName="Vazir", fontSize=8, alignment=1
    )
    style_fee = ParagraphStyle(
        name="fee_style",
        fontName="Vazir",
        fontSize=7,
        alignment=2,
        textColor=colors.dimgrey,
    )
    style_footer = ParagraphStyle(
        name="footer_style", fontName="Vazir", fontSize=9, alignment=2, leading=14
    )
    title_style = ParagraphStyle(
        name="title", fontName="Vazir-Bold", fontSize=16, alignment=1
    )

    visible_table_style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]
    )

    story = []

    logo_path = company_info.get("logo_path")
    if logo_path and os.path.exists(logo_path):
        logo_image = Image(
            logo_path, width=25 * mm, height=25 * mm, kind="proportional"
        )
        header_content = [
            [P(rp("صورتحساب فروش کالا و خدمات"), title_style), logo_image]
        ]
        header_table = Table(header_content, colWidths=[doc.width - 35 * mm, 30 * mm])
        header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(header_table)
    else:
        story.append(P(rp("صورتحساب فروش کالا و خدمات"), title_style))
        story.append(Spacer(1, 4 * mm))

    formatted_invoice_id = f"INV-{invoice_details.get('id', 0):04d}"

    info_data = [
        [
            P(
                rtl(
                    f"تاریخ صدور: {to_persian_digits(invoice_details.get('issue_date', '-'))}"
                ),
                style_right_normal,
            ),
            P(
                rtl(f"شماره فاکتور: {to_persian_digits(formatted_invoice_id)}"),
                style_right_normal,
            ),
        ]
    ]

    story.append(Table(info_data, colWidths=[doc.width / 2, doc.width / 2]))
    story.append(Spacer(1, 2 * mm))

    seller_data_table = [
        [
            P(rp(company_info.get("name", "-")), style_right_normal),
            P(f"<b>{rp('فروشنده:')}</b>", style_right_bold),
        ],
        [
            P(
                to_persian_digits(company_info.get("economic_code", "-")),
                style_right_normal,
            ),
            P(f"<b>{rp('کد اقتصادی:')}</b>", style_right_normal),
        ],
        [
            P(
                to_persian_digits(company_info.get("national_id", "-")),
                style_right_normal,
            ),
            P(f"<b>{rp('شناسه ملی:')}</b>", style_right_normal),
        ],
        [
            P(rp(company_info.get("address", "-")), style_right_normal),
            P(f"<b>{rp('آدرس:')}</b>", style_right_normal),
        ],
        [
            P(to_persian_digits(company_info.get("phone", "-")), style_right_normal),
            P(f"<b>{rp('تلفن:')}</b>", style_right_normal),
        ],
        [
            P(
                to_persian_digits(company_info.get("postal_code", "-")),
                style_right_normal,
            ),
            P(f"<b>{rp('کد پستی:')}</b>", style_right_normal),
        ],
    ]

    buyer_data_table = [
        [
            P(rp(invoice_details.get("customer_name", "-")), style_right_normal),
            P(f"<b>{rp('خریدار:')}</b>", style_right_bold),
        ],
        [
            P(
                to_persian_digits(invoice_details.get("economic_code", "-")),
                style_right_normal,
            ),
            P(f"<b>{rp('کد اقتصادی:')}</b>", style_right_normal),
        ],
        [
            P(
                to_persian_digits(invoice_details.get("national_id", "-")),
                style_right_normal,
            ),
            P(f"<b>{rp('شناسه/کد ملی:')}</b>", style_right_normal),
        ],
        [
            P(rp(invoice_details.get("address", "-")), style_right_normal),
            P(f"<b>{rp('آدرس:')}</b>", style_right_normal),
        ],
        [
            P(to_persian_digits(invoice_details.get("phone", "-")), style_right_normal),
            P(f"<b>{rp('تلفن:')}</b>", style_right_normal),
        ],
        [
            P(
                to_persian_digits(invoice_details.get("postal_code", "-")),
                style_right_normal,
            ),
            P(f"<b>{rp('کد پستی:')}</b>", style_right_normal),
        ],
    ]

    col_widths_contact = [doc.width * 0.3, doc.width * 0.2]
    seller_table_final = Table(seller_data_table, colWidths=col_widths_contact)

    seller_table_final.setStyle(visible_table_style)

    buyer_table_final = Table(buyer_data_table, colWidths=col_widths_contact)
    buyer_table_final.setStyle(visible_table_style)

    contact_container_table = Table(
        [[buyer_table_final, seller_table_final]],
        colWidths=[doc.width / 2, doc.width / 2],
    )
    contact_container_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(contact_container_table)
    story.append(Spacer(1, 5 * mm))

    items_header = [
        P(rp(h), style_center_bold)
        for h in [
            "جمع کل (ریال)",
            "مالیات",
            "جمع پس از تخفیف",
            "تخفیف",
            "مبلغ کل",
            "مبلغ واحد",
            "مقدار",
            "شرح کالا / خدمات",
            "ردیف",
        ]
    ]
    pdf_table_data = [items_header]
    totals = {"c5": 0, "c6": 0, "c7": 0, "c8": 0, "c9": 0}

    for i, item in enumerate(items_data):
        quantity, unit_price = item.get("quantity", 0), item.get("unit_price", 0)
        discount_p, tax_p = item.get("discount_percent", 0), item.get("tax_percent", 0)
        c5, c6 = quantity * unit_price, (quantity * unit_price) * (discount_p / 100)
        c7, c8 = c5 - c6, (c5 - c6) * (tax_p / 100)

        item_extra_costs, extra_costs_details = 0, []
        for fee in item.get("extra_costs", []):
            fee_amount = (
                fee.get("value", 0)
                if fee.get("type") == "amount"
                else c7 * (fee.get("value", 0) / 100)
            )
            item_extra_costs += fee_amount
            extra_costs_details.append(
                P(
                    rp(
                        f"{fee.get('name', '')} (+{to_persian_digits(f'{fee_amount:,.0f}')}) └"
                    ),
                    style_fee,
                )
            )

        c9 = c7 + c8 + item_extra_costs
        for k, v in zip(totals.keys(), [c5, c6, c7, c8, c9]):
            totals[k] += v

        description_cell = [
            P(rp(item.get("description", "")), style_right_normal)
        ] + extra_costs_details

        pdf_table_data.append(
            [
                P(to_persian_digits(f"{c9:,.0f}"), style_center_normal),
                P(to_persian_digits(f"{c8:,.0f}"), style_center_normal),
                P(to_persian_digits(f"{c7:,.0f}"), style_center_normal),
                P(to_persian_digits(f"{c6:,.0f}"), style_center_normal),
                P(to_persian_digits(f"{c5:,.0f}"), style_center_normal),
                P(to_persian_digits(f"{unit_price:,.0f}"), style_center_normal),
                P(to_persian_digits(quantity), style_center_normal),
                description_cell,
                P(to_persian_digits(i + 1), style_center_normal),
            ]
        )

    summary_row = [
        P(f"<b>{to_persian_digits(f'{totals["c9"]:,.0f}')}</b>", style_center_bold),
        P(f"<b>{to_persian_digits(f'{totals["c8"]:,.0f}')}</b>", style_center_bold),
        P(f"<b>{to_persian_digits(f'{totals["c7"]:,.0f}')}</b>", style_center_bold),
        P(f"<b>{to_persian_digits(f'{totals["c6"]:,.0f}')}</b>", style_center_bold),
        P(f"<b>{to_persian_digits(f'{totals["c5"]:,.0f}')}</b>", style_center_bold),
        P(f"<b>{rp('جمع کل')}</b>", style_center_bold),
        "",
        "",
        "",
    ]

    pdf_table_data.append(summary_row)

    items_table = Table(
        pdf_table_data,
        colWidths=[
            doc.width * w for w in [0.15, 0.11, 0.14, 0.1, 0.12, 0.1, 0.06, 0.17, 0.06]
        ],
        repeatRows=1,
    )
    items_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                ("SPAN", (5, -1), (8, -1)),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 5 * mm))

    footer_data = [
        [
            P(
                num_to_words_persian(invoice_details.get("total_amount", 0)),
                style_right_normal,
            ),
            P(f"<b>{rp('مبلغ کل به حروف:')}</b>", style_footer),
        ],
    ]

    pay_method = invoice_details.get("payment_method", "نقدی")
    pay_text = pay_method

    if pay_method == "چکی":
        cheque_number = to_persian_digits(invoice_details.get("cheque_number", "-"))
        cheque_due = to_persian_digits(invoice_details.get("cheque_due_date", "-"))
        pay_text += f" (شماره چک: {cheque_number} | تاریخ سررسید: {cheque_due})"

    footer_data.append(
        [
            P(rtl(pay_text), style_right_normal),
            P(rtl("روش پرداخت:"), style_footer),
        ]
    )

    notes = invoice_details.get("notes", "")
    if notes:
        footer_data.append(
            [
                P(rp(notes), style_right_normal),
                P(f"<b>{rp('توضیحات:')}</b>", style_footer),
            ]
        )

    status_val = invoice_details.get("status")
    status_text, status_color = rp("نامشخص"), colors.black
    if status_val == "پرداخت شده":
        status_text, status_color = rp("پرداخت شده"), colors.darkgreen
    elif status_val == "پرداخت نشده":
        status_text, status_color = rp("پرداخت نشده"), colors.red
    elif status_val == "کسری":
        remaining = invoice_details.get("total_amount", 0) - invoice_details.get(
            "amount_paid", 0
        )
        status_text = rp(f"کسری (مانده: {to_persian_digits(f'{remaining:,.0f}')} ریال)")
        status_color = colors.orange
    status_paragraph = P(
        status_text,
        ParagraphStyle(
            name="status",
            fontName="Vazir-Bold",
            fontSize=10,
            alignment=2,
            textColor=status_color,
        ),
    )
    footer_data.append(
        [status_paragraph, P(f"<b>{rp('وضعیت پرداخت:')}</b>", style_footer)]
    )

    story.append(Table(footer_data, colWidths=[doc.width * 0.75, doc.width * 0.25]))
    story.append(Spacer(1, 8 * mm))

    # --- امضاها ---
    signature_table = Table(
        [
            [
                P(rp("مهر و امضای خریدار"), style_center_bold),
                P(rp("مهر و امضای فروشنده"), style_center_bold),
            ]
        ],
        colWidths=[doc.width * 0.5, doc.width * 0.5],
        rowHeights=20 * mm,
    )
    signature_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(signature_table)

    try:
        doc.build(story)
        return file_path, True
    except Exception:
        return traceback.format_exc(), False
