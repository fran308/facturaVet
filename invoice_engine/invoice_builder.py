# invoice_builder.py
from invoice_service import (
    get_initial_invoice_status,
    requires_verifactu_submission
)

# Importar la función para dirección completa
from client_fields import get_full_address


def build_invoice_object(
    session_state,
    invoice_type,
    invoice_items,
    totals,
    irpf_data,
    username,
    is_b2b
):
    # ... tus cálculos existentes ...
    
    # Crear una copia del cliente para no modificar el original
    client_data = session_state.client.copy()
    
    # Añadir campo calculado (dirección completa)
    client_data["full_address"] = get_full_address(session_state.client)
    
    # Mantener campo 'address' legacy para compatibilidad
    if not client_data.get("address"):
        client_data["address"] = client_data["full_address"]
    
    invoice_data = {
        "header": {
            "invoice_number": session_state.invoice_number,
            "invoice_type": invoice_type,
            "invoice_date": session_state.invoice_date.isoformat(),
            "operation_date": session_state.operation_date.isoformat(),
            "created_by": username,
        },
        
        # CLIENTE: TODO el diccionario
        "client": client_data,
        
        "items": invoice_items,
        
        "totals": {
            "total_gross": round(totals["total_gross"], 2),
            "total_net": round(totals["total_net"], 2),
            "total_vat": round(totals["total_vat"], 2),
            "total_vat_21": round(totals["total_vat_21"], 2),
            "total_vat_10": round(totals["total_vat_10"], 2),
            "irpf_total": round(irpf_data["irpf_total"], 2),
            "final_payable": round(irpf_data["final_payable"], 2),
        },
        
        "status": {
            "invoice_status": get_initial_invoice_status(),
            "verifactu_required": requires_verifactu_submission(
                is_b2b=is_b2b,
                total_gross=totals["total_gross"],
                client_requested_invoice=(
                    invoice_type != "B2C • Factura simplificada"
                )
            ),
            "verifactu_submitted": False,
            "payment_link_created": False,
            "paid": False,
        }
    }
    
    return invoice_data
