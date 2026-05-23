# company_config.py
"""
CONFIGURACIÓN DE FORMATO DE FACTURA
====================================
Este archivo contiene la estructura y formato de las facturas,
pero NO datos sensibles (que están en st.secrets)

Puede subirse a GitHub sin problemas.
"""

def get_company_data_from_secrets():
    """
    Carga los datos de la empresa desde st.secrets
    Esta función es la única que accede a los secretos
    """
    import streamlit as st
    
    # Verificar que los secretos existen
    if "company" not in st.secrets:
        st.error("⚠️ Configuración de empresa no encontrada en secrets.toml")
        return None
    
    company = st.secrets["company"]
    
    # Construir dirección completa
    address = company["address"]
    full_address = f"{address['street']}. {address['street_number']}, {address['postal_code']}, {address['city']}, {address['province']}"
    
    return {
        "legal_name": company["legal_name"],
        "trading_name": company["trading_name"],
        "nif": company["nif"],
        "specialty": company["specialty"],
        "address": full_address,
        "address_parts": dict(address),  # versión estructurada
        "phone": company["contact"]["phone"],
        "email": company["contact"]["email"],
        "bank": dict(company["bank"]),
        "payment_terms": dict(company["payment_terms"])
    }


# =========================================================
# CONFIGURACIÓN DE FORMATO (OJO VETERINARIO BRANDING)
# =========================================================

# Estilos de la factura con la paleta de Ojo Veterinario
INVOICE_STYLES = {
    "primary_color": "#a747a2",      # Magenta/Púrpura corporativo para elementos principales
    "secondary_color": "#f6ebf5",    # Tono pastel suave derivado para fondos de totales
    "text_color": "#333333",
    "muted_color": "#666666",
    "footer_color": "#888888",
}

# Estructura de la tabla (qué columnas mostrar según tipo)
TABLE_COLUMNS = {
    "b2b": ["Concepto", "Base Imponible", "Tipo IVA", "Cuota IVA", "Importe Total"],
    "b2c_full": ["Concepto", "Base Imponible", "Tipo IVA", "Cuota IVA", "Importe Total"],
    "b2c_simplified": ["Concepto", "Base Imponible", "Tipo IVA", "Cuota IVA", "Importe Total"]
}

# Textos del pie de página (plantillas)
FOOTER_TEMPLATES = {
    "b2b": """
        <b>Gracias por confiar en {trading_name}</b><br/>
        {legal_name}<br/>
        Método de pago por {payment_method} | {bank_name} BIC: {bic} IBAN: {iban}<br/>
        Vencimiento en {days} días - Tel: {phone} | E-mail: {email}
    """,
    "b2c_full": """
        <b>Gracias por su confianza</b><br/>
        {trading_name} - {legal_name}<br/>
        Tel: {phone} | {email}
    """,
    "b2c_simplified": "Factura simplificada - {trading_name}"
}


def get_footer_text(invoice_type, company_data):
    """
    Genera el texto del pie de página según tipo de factura
    """
    import streamlit as st
    
    if invoice_type == "B2B • Profesional con IRPF":
        template = FOOTER_TEMPLATES["b2b"]
    elif invoice_type == "B2C • Factura simplificada":
        template = FOOTER_TEMPLATES["b2c_simplified"]
    else:
        template = FOOTER_TEMPLATES["b2c_full"]
    
    # Datos bancarios
    bank = company_data["bank"]
    payment = company_data["payment_terms"]
    
    return template.format(
        trading_name=company_data["trading_name"],
        legal_name=company_data["legal_name"],
        payment_method=payment["method"],
        bank_name=bank["name"],
        bic=bank["bic"],
        iban=bank["iban"],
        days=payment["days"],
        phone=company_data["phone"],
        email=company_data["email"]
    )
