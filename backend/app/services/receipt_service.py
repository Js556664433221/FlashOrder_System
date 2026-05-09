from io import BytesIO
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class ReceiptPDFService:
    """Service for generating Official Receipt (OR) PDF documents."""

    COMPANY_NAME = "FlashOrder Portal"
    COMPANY_ADDRESS = "123 Commerce Street, Business District"
    COMPANY_CONTACT = "Tel: (555) 123-4567"

    @staticmethod
    def generate_receipt_pdf(
        or_number: str,
        order_number: str,
        timestamp: datetime,
        customer_name: str,
        delivery_method: str,
        address: Optional[str],
        items: list,
        subtotal: float,
        discount_amount: float,
        total_price: float,
    ) -> BytesIO:
        """Generate a PDF official receipt.

        Args:
            or_number: Official Receipt number
            order_number: Order reference number
            timestamp: Order creation timestamp
            customer_name: Customer's name
            delivery_method: "Delivery" or "Pickup"
            address: Delivery address (if delivery)
            items: List of item dicts with product_name, quantity, unit_price
            subtotal: Subtotal before discount
            discount_amount: Discount amount applied
            total_price: Final total price

        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=6,
            alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=4
        )
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=4
        )
        normal_style = ParagraphStyle(
            'NormalText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=2
        )
        right_style = ParagraphStyle(
            'RightText',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        )

        elements = []

        # Company header
        elements.append(Paragraph(ReceiptPDFService.COMPANY_NAME, title_style))
        elements.append(Paragraph(ReceiptPDFService.COMPANY_ADDRESS, subtitle_style))
        elements.append(Paragraph(ReceiptPDFService.COMPANY_CONTACT, subtitle_style))
        elements.append(Spacer(1, 10))

        # Receipt title
        elements.append(Paragraph("<b>OFFICIAL RECEIPT</b>", title_style))
        elements.append(Spacer(1, 10))

        # OR Number and Date
        or_info = [
            [Paragraph(f"<b>OR Number:</b> {or_number}", normal_style),
             Paragraph(f"<b>Date:</b> {timestamp.strftime('%B %d, %Y')}", normal_style)],
            [Paragraph(f"<b>Order Number:</b> {order_number}", normal_style),
             Paragraph(f"<b>Time:</b> {timestamp.strftime('%I:%M %p')}", normal_style)],
        ]
        or_table = Table(or_info, colWidths=[100*mm, 70*mm])
        or_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(or_table)
        elements.append(Spacer(1, 8))

        # Customer info
        elements.append(Paragraph("<b>Customer Information</b>", header_style))
        elements.append(Paragraph(f"Customer Name: {customer_name}", normal_style))
        elements.append(Paragraph(f"Delivery Method: {delivery_method}", normal_style))
        if delivery_method == "Delivery" and address:
            elements.append(Paragraph(f"Delivery Address: {address}", normal_style))
        elements.append(Spacer(1, 10))

        # Items table header
        elements.append(Paragraph("<b>Order Details</b>", header_style))

        # Build items table
        table_data = [
            ["#", "Product Name", "Qty", "Unit Price", "Subtotal"]
        ]

        for idx, item in enumerate(items, 1):
            product_name = item.get('product_name', 'Unknown Product')
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0.0)
            item_subtotal = quantity * unit_price

            table_data.append([
                str(idx),
                product_name[:40],  # Truncate long names
                str(quantity),
                f"RM {unit_price:,.2f}",
                f"RM {item_subtotal:,.2f}"
            ])

        # Create table
        items_table = Table(table_data, colWidths=[15*mm, 80*mm, 20*mm, 30*mm, 35*mm])
        items_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            # Alignment
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # # column
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Qty column
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),   # Prices
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2C3E50')),
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 10))

        # Totals section
        totals_data = [
            [Paragraph("Subtotal:", normal_style), Paragraph(f"RM {subtotal:,.2f}", right_style)],
        ]

        if discount_amount > 0:
            totals_data.append([
                Paragraph("Discount:", normal_style),
                Paragraph(f"-RM {discount_amount:,.2f}", right_style)
            ])

        totals_data.append([
            Paragraph("<b>TOTAL:</b>", ParagraphStyle('Total', parent=normal_style, fontName='Helvetica-Bold', fontSize=12)),
            Paragraph(f"<b>RM {total_price:,.2f}</b>", ParagraphStyle('TotalAmt', parent=right_style, fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#27AE60')))
        ])

        totals_table = Table(totals_data, colWidths=[120*mm, 50*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#2C3E50')),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
            ('TOPPADDING', (0, -1), (-1, -1), 8),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 20))

        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.gray
        )
        elements.append(Paragraph("─" * 80, footer_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("Thank you for your business!", footer_style))
        elements.append(Paragraph("This serves as your official receipt.", footer_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
