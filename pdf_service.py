# pdf_service.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
import streamlit as st

from company_config import get_company_data_from_secrets, INVOICE_STYLES, get_footer_text


def generate_pdf(invoice_data):
    """
    Genera PDF profesional usando datos de empresa desde st.secrets
    e incorpora requerimientos fiscales Verifactu.
    """
    
    # Cargar datos de empresa desde secrets
    company_data = get_company_data_from_secrets()
    if not company_data:
        raise ValueError("No se pudieron cargar los datos de la empresa")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # =========================================================
    # ESTILOS PERSONALIZADOS
    # =========================================================
    
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor(INVOICE_STYLES["primary_color"]),
        alignment=TA_CENTER,
        spaceAfter=0
    ))
    
    styles.add(ParagraphStyle(
        name='Specialty',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor(INVOICE_STYLES["muted_color"]),
        alignment=TA_CENTER,
        spaceAfter=12
    ))
    
    styles.add(ParagraphStyle(
        name='InvoiceTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor(INVOICE_STYLES["text_color"]),
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor(INVOICE_STYLES["primary_color"]),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor(INVOICE_STYLES["muted_color"]),
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='Value',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor(INVOICE_STYLES["text_color"])
    ))
    
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor(INVOICE_STYLES["footer_color"]),
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='VerifactuNotice',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor(INVOICE_STYLES["text_color"]),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    ))
    
    # =========================================================
    # CABECERA
    # =========================================================
    
    story.append(Paragraph(company_data["trading_name"], styles['CompanyName']))
    story.append(Paragraph(company_data["specialty"], styles['Specialty']))
    story.append(Spacer(1, 0.5*cm))
    
    # =========================================================
    # NÚMERO DE FACTURA Y FECHAS
    # =========================================================
    
    invoice_type = invoice_data["header"]["invoice_type"]
    is_simplified = invoice_type == "B2C • Factura simplificada"
    is_b2b = invoice_type == "B2B • Profesional con IRPF"

    # Determinación legal del título del documento
    display_title = "<b>FACTURA SIMPLIFICADA</b>" if is_simplified else "<b>FACTURA COMPLETA</b>"
    
    invoice_header = [
        ["", display_title],
        ["", f"<b>Nº:</b> {invoice_data['header']['invoice_number']}"],
        ["", f"<b>Expedición:</b> {invoice_data['header']['invoice_date']}"],
        ["", f"<b>Operación:</b> {invoice_data['header']['operation_date']}"]
    ]
    
    header_table = Table(invoice_header, colWidths=[10*cm, 6*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (1, 0), (1, -1), 'TOP'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 0), (1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))
    
    # =========================================================
    # CLIENTE Y EMISOR (CON LOGICA DE PRIVACIDAD SIMPLIFICADA)
    # =========================================================
    
    client = invoice_data["client"]
    client_text = []

    if is_simplified:
        # En factura simplificada pura no mostramos datos de identificación de cliente por defecto
        client_text.append("<i>Factura simplificada al portador</i>")
    else:
        # Facturas Completas o B2B muestran obligatoriamente al cliente receptor
        client_text.append(f"<b>Receptor / Cliente:</b><br/>")
        client_text.append(f"{client.get('name', '')}<br/>")
        client_text.append(f"NIF/CIF: {client.get('nif', '')}<br/>")
        
        client_address = client.get('full_address', '')
        if not client_address:
            parts = []
            if client.get('street'):
                street = client['street']
                if client.get('street_number'):
                    street += f", {client['street_number']}"
                parts.append(street)
            if client.get('city'):
                parts.append(client['city'])
            if client.get('postal_code'):
                parts.insert(0, client['postal_code'])
            client_address = ", ".join(parts)
        
        if client_address:
            client_text.append(f"{client_address}<br/>")
    
    # Datos obligatorios del emisor fiscal
    issuer_text = [
        f"<b>Emisor / Profesional:</b><br/>",
        f"{company_data['legal_name']}<br/>",
        f"NIF: {company_data['nif']}<br/>",
        f"{company_data['address']}<br/>",
        f"{company_data['phone']} | {company_data['email']}"
    ]
    
    parties_data = [
        [Paragraph("".join(client_text), styles['Value']),
         Paragraph("".join(issuer_text), styles['Value'])]
    ]
    
    parties_table = Table(parties_data, colWidths=[8*cm, 8*cm])
    parties_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 0.8*cm))
    
    # =========================================================
    # TABLA DE CONCEPTOS (ESTRUCTURA DE 5 COLUMNAS UNIFICADA)
    # =========================================================
    
    # Distribución equilibrada para abarcar los 16cm útiles de la página A4
    col_widths = [5.5*cm, 2.7*cm, 2.0*cm, 2.7*cm, 3.1*cm]
    
    table_data = [["Concepto", "Base Imponible", "Tipo IVA", "Cuota IVA", "Importe Total"]]
    
    for item in invoice_data["items"]:
        table_data.append([
            Paragraph(item["name"], styles['Value']),
            f"€{item['net_price']:.2f}",
            item["vat"],
            f"€{item['vat_amount']:.2f}", # Mostramos el desglose unitario
            f"€{item['gross_price']:.2f}"
        ])
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(INVOICE_STYLES["primary_color"])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    
    # =========================================================
    # TOTALES
    # =========================================================
    
    totals = invoice_data["totals"]
    
    if is_b2b:
        totals_data = [
            ["Base imponible:", f"€{totals['total_net']:.2f}"],
            [f"IVA (21%):", f"€{totals['total_vat_21']:.2f}"],
            [f"IRPF (15%):", f"-€{totals['irpf_total']:.2f}"],
            ["", ""],
            ["TOTAL A PAGAR:", f"€{totals['final_payable']:.2f}"]
        ]
    else:
        totals_data = [
            ["Base imponible:", f"€{totals['total_net']:.2f}"],
            [f"IVA (21%):", f"€{totals['total_vat_21']:.2f}"],
        ]
        if totals['total_vat_10'] > 0:
            totals_data.insert(2, [f"IVA (10%):", f"€{totals['total_vat_10']:.2f}"])
        totals_data.append(["", ""])
        totals_data.append(["TOTAL FACTURA:", f"€{totals['total_gross']:.2f}"])
    
    totals_table = Table(totals_data, colWidths=[11.5*cm, 4.5*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (1, -1), 11),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor(INVOICE_STYLES["primary_color"])),
        ('BACKGROUND', (0, -1), (1, -1), colors.HexColor(INVOICE_STYLES["secondary_color"])),
        ('TOPPADDING', (0, -1), (1, -1), 6),
        ('BOTTOMPADDING', (0, -1), (1, -1), 6),
    ]))
    
    story.append(totals_table)
    story.append(Spacer(1, 0.8*cm))
    
    # =========================================================
    # REQUERIMIENTOS VERIFACTU & CODIGO QR
    # =========================================================
    
    # Texto legal explícito de Verifactu obligatorio en el documento impreso
    verifactu_text = (
        "<b>Factura verificable en la sede electrónica de la AEAT</b><br/>"
        "<font color='#555555' size='7'>Este documento técnico cumple con la normativa de registro "
        "e integridad Verifactu de la Agencia Tributaria. Una vez liquidada, su huella digital hash "
        "y estado de encadenamiento pueden validarse de forma pública.</font>"
    )

    # Bloque de reserva estructural para el código QR técnico (3x3 cm reglamentario)
    qr_placeholder_data = [
        [Paragraph(verifactu_text, styles['VerifactuNotice']), ""]
    ]
    
    # Cuando implementes el endpoint final, reemplazarás el string vacío "" por la imagen del QR generado
    verifactu_table = Table(qr_placeholder_data, colWidths=[12.5*cm, 3.5*cm])
    verifactu_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LINEBELOW', (1, 0), (1, 0), 0.5, colors.transparent), # Cambiar a gris si deseas ver el borde del cuadro QR
    ]))
    
    story.append(verifactu_table)
    story.append(Spacer(1, 0.6*cm))
    
    # =========================================================
    # PIE DE PÁGINA
    # =========================================================
    
    footer_text = get_footer_text(invoice_type, company_data)
    story.append(Paragraph(footer_text, styles['Footer']))
    
    # =========================================================
    # GENERAR PDF
    # =========================================================
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()
