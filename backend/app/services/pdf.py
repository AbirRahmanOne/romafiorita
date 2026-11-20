"""Branded 'Order summary / Payment request' PDF (spec §F).

Pure-Python (fpdf2 + segno) so it needs no system libraries. It is deliberately
NOT labelled a fiscal invoice ('fattura') — there is no VAT number yet.
"""

from __future__ import annotations

import io

import segno
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.models import PaymentRequest

# Business identity placeholders (nullable in settings until the client supplies).
_BUSINESS = (
    "Roma Fiorita · [legal name] · [Rome address] · P.IVA [n/a] · tel [phone]"
)


def _s(text: str) -> str:
    """Core fonts are latin-1 only; drop anything they can't encode."""
    return text.encode("latin-1", "replace").decode("latin-1")


def _euro(cents: int) -> str:
    return f"EUR {cents / 100:.2f}"


def generate_payment_request_pdf(
    pr: PaymentRequest,
    *,
    order_number: str,
    pay_url: str,
    title: str = "Payment request",
) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    def line(text: str, size: int = 11, style: str = "") -> None:
        pdf.set_font("Helvetica", style, size)
        pdf.cell(0, 8, _s(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    line("Roma Fiorita", size=20, style="B")
    line(title, size=14, style="B")  # not "fattura"
    line(f"Order {order_number}")
    line(f"Recipient: {pr.recipient or '-'}")
    line(f"Delivery: {pr.delivery_slot or '-'}")
    pdf.ln(3)

    for item in pr.items:
        line(f"{item['title']}    {_euro(item['price_cents'])}")
    if pr.discount_cents:
        line(f"Discount    -{_euro(pr.discount_cents)}")
    line(f"Total    {_euro(pr.amount_cents)}", size=12, style="B")
    pdf.ln(2)

    line(f"Pay online: {pay_url}")
    line(f"Expires: {pr.expires_at.isoformat()}")

    qr = segno.make(pay_url, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=4)
    buf.seek(0)
    pdf.image(buf, w=35)

    pdf.ln(2)
    pdf.set_font("Helvetica", size=8)
    pdf.multi_cell(0, 4, _s(f"{_BUSINESS}\nThis document is not a fiscal invoice."))

    return bytes(pdf.output())
