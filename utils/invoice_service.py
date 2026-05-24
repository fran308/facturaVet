# =========================================================
# INVOICE TYPE FLAGS
# =========================================================

def get_invoice_type_flags(invoice_type):

    requires_client_details = (
        invoice_type != "B2C • Factura simplificada"
    )

    is_b2b = (
        invoice_type == "B2B • Profesional con IRPF"
    )

    is_simplified_invoice = (
        invoice_type == "B2C • Factura simplificada"
    )

    return (
        requires_client_details,
        is_b2b,
        is_simplified_invoice
    )


# =========================================================
# VALIDATE INVOICE
# =========================================================

def validate_invoice(
    invoice_number,
    invoice_items,
    requires_client_details=False,
    client_data=None  # ← diccionario, no campos individuales
):
    # -----------------------------------------------------
    # INVOICE NUMBER
    # -----------------------------------------------------
    if not invoice_number:
        return "❌ Enter invoice number first"
    
    # -----------------------------------------------------
    # ITEMS
    # -----------------------------------------------------
    if not invoice_items:
        return "❌ No items in invoice"
    
    # -----------------------------------------------------
    # CLIENT DETAILS
    # -----------------------------------------------------
    if requires_client_details:
        from client_fields import validate_client
        error = validate_client(client_data or {})
        if error:
            return error
    
    return None

# =========================================================
# PAYABLE ITEMS
# =========================================================

def get_payable_items(invoice_items):

    return [

        item for item
        in invoice_items

        if item["gross_price"] > 0
    ]


# =========================================================
# TOTAL TITLE
# =========================================================

def build_total_title(
    is_b2b,
    final_payable,
    total_gross
):

    if is_b2b:

        return (
            f"### 💰 Amount company pays: "
            f"€{final_payable:.2f}"
        )

    return (
        f"### 💰 Total client pays: "
        f"€{total_gross:.2f}"
    )


# =========================================================
# TOTAL CAPTION
# =========================================================

def build_total_caption(
    is_b2b,
    total_net,
    total_vat_21,
    total_vat_10,
    irpf_total
):

    if is_b2b:

        return (
            f"Base imponible: €{total_net:.2f} | "
            f"IVA 21%: €{total_vat_21:.2f} | "
            f"IVA 10%: €{total_vat_10:.2f} | "
            f"IRPF 15%: -€{irpf_total:.2f}"
        )

    return (
        f"Net: €{total_net:.2f} | "
        f"IVA 21%: €{total_vat_21:.2f} | "
        f"IVA 10%: €{total_vat_10:.2f}"
    )


# =========================================================
# INVOICE STATUS
# =========================================================

def get_initial_invoice_status():

    return "DRAFT"


# =========================================================
# VERIFACTU READINESS
# =========================================================

def requires_verifactu_submission(
    is_b2b,
    total_gross,
    client_requested_invoice=False
):

    # -----------------------------------------------------
    # B2B ALWAYS REQUIRES VERIFACTU
    # -----------------------------------------------------

    if is_b2b:

        return True

    # -----------------------------------------------------
    # B2C >= 400€
    # -----------------------------------------------------

    if total_gross >= 400:

        return True

    # -----------------------------------------------------
    # CLIENT REQUESTED FULL INVOICE
    # -----------------------------------------------------

    if client_requested_invoice:

        return True

    # -----------------------------------------------------
    # OTHERWISE SIMPLIFIED TICKET
    # -----------------------------------------------------

    return False


# =========================================================
# STRIPE ELIGIBILITY
# =========================================================

def can_generate_payment_link(
    invoice_status
):

    allowed_statuses = [

        "DRAFT",
        "READY_FOR_PAYMENT"
    ]

    return invoice_status in allowed_statuses
