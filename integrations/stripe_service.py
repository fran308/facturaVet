import stripe

from datetime import (
    datetime,
    timedelta
)

# =========================================================
# BUILD LINE ITEMS
# =========================================================

def build_line_items(
    payable_items,
    is_b2b,
    final_payable,
    invoice_number
):

    line_items = []

    # -----------------------------------------------------
    # B2B WITH IRPF
    # -----------------------------------------------------

    if is_b2b:

        line_items.append({

            "price_data": {

                "currency": "eur",

                "unit_amount": int(
                    round(final_payable * 100)
                ),

                "product_data": {

                    "name": (
                        f"Invoice {invoice_number}"
                    )
                },
            },

            "quantity": 1,
        })

    # -----------------------------------------------------
    # NORMAL INVOICES
    # -----------------------------------------------------

    else:

        for item in payable_items:

            unit_amount_cents = int(
                round(item["gross_price"] * 100)
            )

            line_items.append({

                "price_data": {

                    "currency": "eur",

                    "unit_amount":
                        unit_amount_cents,

                    "product_data": {

                        "name":
                            f"{item['name']} "
                            "(IVA incluido)"
                    },
                },

                "quantity": 1,
            })

    return line_items


# =========================================================
# BUILD METADATA
# =========================================================

def build_metadata(
    session_state,
    total_gross,
    total_net,
    total_vat,
    irpf_total,
    final_payable,
    username
):
    client = session_state.client

    return {
        "invoice_number": session_state.invoice_number,
        "invoice_date": session_state.invoice_date.isoformat(),
        "operation_date": session_state.operation_date.isoformat(),
        
        "total_gross": str(round(total_gross, 2)),
        "total_net": str(round(total_net, 2)),
        "total_vat": str(round(total_vat, 2)),
        "irpf_total": str(round(irpf_total, 2)),
        "final_payable": str(round(final_payable, 2)),
        
        "created_by": username,
        
        # Cliente (solo campos esenciales por límite de caracteres)
        "client_name": client.get("name", ""),
        "client_nif": client.get("nif", ""),
        "client_email": client.get("email", ""),
        "client_phone": client.get("phone", ""),
    }


# =========================================================
# CREATE CHECKOUT SESSION
# =========================================================

def create_checkout_session(
    line_items,
    metadata
):

    expires_at = int(

        (
            datetime.utcnow()
            + timedelta(hours=23)
        ).timestamp()
    )

    return stripe.checkout.Session.create(

        line_items=line_items,

        mode="payment",

        success_url=(
            "https://ojoveterinario.es/"
            "thankyou-payment"
        ),

        cancel_url=(
            "https://ojoveterinario.es/"
            "payment-cancelled"
        ),

        billing_address_collection="auto",

        phone_number_collection={
            "enabled": True
        },

        customer_creation="always",

        expires_at=expires_at,

        metadata=metadata
    )
