# invoice_engine/pdf_service.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
import streamlit as st
from datetime import date, datetime

from invoice_engine.company_config import get_company_data_from_secrets, INVOICE_STYLES, get_footer_text


def generate_pdf(invoice_data):
    """
    Genera PDF profesional usando datos de empresa desde st.secrets
    e incorpora requerimientos fiscales Verifactu (bloque técnico comentado).
    Control de estilos, formato de fecha (dd/mm/yyyy), visibilidad de fechas 
    y datos de cliente manejados 100% de forma nativa.
    """
    
    # Cargar datos de empresa desde secrets
    company_data = get_company_data_from_secrets()
    if not company_data:
        raise ValueError("No se pudieron cargar los datos de la empresa")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.8*cm,
        bottomMargin=1.8*cm,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # =========================================================
    # ESTILOS PERSONALIZADOS
    # =========================================================
    
    # 💡 OJO VETERINARIO ahora en color negro (#333333) para mejor contraste de marca
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor(INVOICE_STYLES["text_color"]),
        alignment=TA_CENTER,
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='Specialty',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor(INVOICE_STYLES["muted_color"]),
        alignment=TA_CENTER,
        spaceAfter=15
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
        name='Value',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor(INVOICE_STYLES["text_color"]),
        leading=13
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
        alignment=TA_LEFT,
        leading=11
    ))
    
    # =========================================================
    # CABECERA
    # =========================================================
    
    story.append(Paragraph(company_data["trading_name"], styles['CompanyName']))
    story.append(Paragraph(company_data["specialty"], styles['Specialty']))
    story.append(Spacer(1, 0.4*cm))
    
    # =========================================================
    # NÚMERO DE FACTURA Y FECHAS (FORMATO DD/MM/YYYY)
    # =========================================================
    
    invoice_type = invoice_data["header"]["invoice_type"]
    is_simplified = invoice_type == "B2C • Factura simplificada"
    is_b2b = invoice_type == "B2B • Profesional con IRPF"

    # Determinación del título del documento
    display_title = "FACTURA SIMPLIFICADA" if is_simplified else "FACTURA COMPLETA"
    
    # 💡 Conversión segura de formatos de fecha a dd/mm/yyyy
    def format_to_spanish_date(date_input):
        if isinstance(date_input, (date, datetime)):
            return date_input.strftime("%d/%m/%Y")
        try:
            # Por si viene como string tipo ISO (yyyy-mm-dd) desde el estado anterior
            parsed_date = datetime.strptime(str(date_input), "%Y-%m-%d")
            return parsed_date.strftime("%d/%m/%Y")
        except ValueError:
            return str(date_input)

    formatted_expedition = format_to_spanish_date(invoice_data['header']['invoice_date'])
    
    # Estructura base de la cabecera
    invoice_header = [
        ["", display_title],
        ["", f"Nº: {invoice_data['header']['invoice_number']}"],
        ["", f"Expedición: {formatted_expedition}"]
    ]
    
    # Solo mostramos 'Operación' formateada si NO es simplificada
    if not is_simplified:
        formatted_operation = format_to_spanish_date(invoice_data['header']['operation_date'])
        invoice_header.append(["", f"Operación: {formatted_operation}"])
    
    # Tabla de metadatos derecha
    header_table = Table(invoice_header, colWidths=[9.4*cm, 7.0*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (1, 0), (1, -1), 'TOP'),
        
        # Estilo del título principal
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, 0), 12),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor(INVOICE_STYLES["primary_color"])),
        
        # Fechas secundarias
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 1), (1, -1), 9),
        
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.6*cm))
    
    # =========================================================
    # CLIENTE Y EMISOR
    # =========================================================
    
    client = invoice_data["client"]
    client_text = []

    has_client_details = client.get('name', '').strip() != "" or client.get('nif', '').strip() != ""

    if is_simplified:
        if has_client_details:
            client_text.append("Identificación del Destinatario:\n")
            client_text.append(f"{client.get('name', '')}\n")
            if client.get('nif', ''):
                client_text.append(f"NIF/CIF: {client.get('nif', '')}\n")
        else:
            client_text.append("Factura simplificada al portador")
    else:
        client_text.append("Receptor / Cliente:\n")
        client_text.append(f"{client.get('name', '')}\n")
        client_text.append(f"NIF/CIF: {client.get('nif', '')}\n")
        
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
            client_text.append(f"{client_address}\n")
    
    # Datos fijos del emisor profesional
    issuer_text = [
        "Emisor / Profesional:\n",
        f"{company_data['legal_name']}\n",
        f"NIF: {company_data['nif']}\n",
        f"{company_data['address']}\n",
        f"{company_data['phone']} | {company_data['email']}"
    ]
    
    client_paragraph = Paragraph("".join(client_text).replace('\n', '<br/>'), styles['Value'])
    issuer_paragraph = Paragraph("".join(issuer_text).replace('\n', '<br/>'), styles['Value'])
    
    parties_data = [[client_paragraph, issuer_paragraph]]
    
    parties_table = Table(parties_data, colWidths=[8.2*cm, 8.2*cm])
    parties_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('RIGHTPADDING', (0, 0), (0, -1), 15),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 0.8*cm))
    
    # =========================================================
    # TABLA DE CONCEPTOS
    # =========================================================
    
    col_widths = [5.6*cm, 2.7*cm, 2.0*cm, 2.7*cm, 3.4*cm]
    table_data = [["Concepto", "Base Imponible", "Tipo IVA", "Cuota IVA", "Importe Total"]]
    
    for item in invoice_data["items"]:
        table_data.append([
            Paragraph(item["name"], styles['Value']),
            f"{item['net_price']:.2f} €",
            item["vat"],
            f"{item['vat_amount']:.2f} €",
            f"{item['gross_price']:.2f} €"
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
    story.append(Spacer(1, 0.6*cm))
    
    # =========================================================
    # TOTALES
    # =========================================================
    
    totals = invoice_data["totals"]
    
    if is_b2b:
        totals_data = [
            ["Base imponible:", f"{totals['total_net']:.2f} €"],
            ["IVA (21%):", f"{totals['total_vat_21']:.2f} €"],
            ["IRPF (15%):", f"-{totals['irpf_total']:.2f} €"],
            ["", ""],
            ["TOTAL A PAGAR:", f"{totals['final_payable']:.2f} €"]
        ]
    else:
        totals_data = [
            ["Base imponible:", f"{totals['total_net']:.2f} €"],
            ["IVA (21%):", f"{totals['total_vat_21']:.2f} €"],
        ]
        if totals['total_vat_10'] > 0:
            totals_data.insert(2, ["IVA (10%):", f"{totals['total_vat_10']:.2f} €"])
        totals_data.append(["", ""])
        totals_data.append(["TOTAL FACTURA:", f"{totals['total_gross']:.2f} €"])
    
    totals_table = Table(totals_data, colWidths=[11.7*cm, 4.7*cm])
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
    # REQUERIMIENTOS VERIFACTU & CODIGO QR (COMENTADO PROVISIONALMENTE)
    # =========================================================
    # 
    # verifactu_html = (
    #     "<b>Factura verificable en la sede electrónica de la AEAT</b><br/>"
    #     "<font color='#555555' size='7'>Este documento técnico cumple con la normativa de registro "
    #     "e integridad Verifactu de la Agencia Tributaria. Una vez liquidada, su huella digital hash "
    #     "y estado de encadenamiento pueden validarse de forma pública.</font>"
    # )
    #
    # qr_placeholder_data = [
    #     [Paragraph(verifactu_html, styles['VerifactuNotice']), ""]
    # ]
    # 
    # verifactu_table = Table(qr_placeholder_data, colWidths=[12.9*cm, 3.5*cm])
    # verifactu_table.setStyle(TableStyle([
    #     ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #     ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    # ]))
    # 
    # story.append(verifactu_table)
    # story.append(Spacer(1, 0.6*cm))
    
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
