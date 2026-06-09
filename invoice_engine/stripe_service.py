# invoice_engine/stripe_service.py
import stripe
import streamlit as st

# Inicializar la API Key de Stripe desde tus secrets
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

def generate_premium_payment_link(invoice_number, final_payable):
    """
    Genera un precio dinámico y un Payment Link corto nativo de Stripe
    """
    try:
        # 1. Crear el precio en céntimos basado en el total de la factura
        amount_in_cents = int(round(final_payable * 100))
        
        stripe_price = stripe.Price.create(
            currency="eur",
            unit_amount=amount_in_cents,
            product_data={"name": f"Factura #{invoice_number} - Ojo Veterinario"},
        )

        # 2. Crear el Payment Link corto apuntando a ese precio
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": stripe_price.id, "quantity": 1}],
        )

        # 3. Retornar la URL corta nativa (buy.stripe.com/...)
        return payment_link.url

    except Exception as e:
        st.error(f"❌ Error al generar el enlace de Stripe: {e}")
        return None
