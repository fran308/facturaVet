import streamlit as st
import stripe

from datetime import date, datetime, timedelta

import streamlit_authenticator as stauth

from ui_styles.styles import load_css
from config.session_state import initialize_session_state

from utils.calculations import (
    calculate_invoice_item,
    calculate_totals,
    calculate_irpf
)

from integrations.stripe_service import (
    build_line_items,
    build_metadata,
    create_checkout_session
)

from invoice_engine.invoice_service import (
    get_invoice_type_flags,
    validate_invoice,
    get_payable_items,
    build_total_title,
    build_total_caption
)

from invoice_engine.invoice_builder import (
    build_invoice_object
)

from config.client_fields import CLIENT_FIELDS, get_fields_by_section, get_full_address, validate_client

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="FacturaVET • Ojo Veterinario",
    layout="centered"
)

# =========================================================
# AUTHENTICATION
# =========================================================

config = {
    "credentials": {
        "usernames": {
            "fran": {
                "email": "fran@ojoveterinario.es",
                "name": "Fran",
                "password": st.secrets["usernames"]["fran"]["password"]
            },
            "contacto": {
                "email": "contacto@ojoveterinario.es",
                "name": "Contacto",
                "password": st.secrets["usernames"]["contacto"]["password"]
            }
        }
    },
    "cookie": {
        "expiry_days": st.secrets["cookie_expiry_days"],
        "key": st.secrets["cookie_key"],
        "name": st.secrets["cookie_name"]
    },
    "preauthorized": {
        "emails": []
    }
}

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

authenticator.login(location="main")

if st.session_state["authentication_status"]:

    st.sidebar.success(
        f"✅ Bienvenido {st.session_state['name']}"
    )

    authenticator.logout(
        "Cerrar sesión",
        location="sidebar"
    )

elif st.session_state["authentication_status"] is False:

    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

elif st.session_state["authentication_status"] is None:

    st.title("🔐 FacturaVET")
    st.caption("Secure veterinary payment link generator")
    st.warning("Introduce usuario y contraseña")
    st.stop()

username = st.session_state["username"]

# =========================================================
# STRIPE CONFIG
# =========================================================

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

# =========================================================
# LOAD CSS
# =========================================================

load_css()

# =========================================================
# SESSION STATE
# =========================================================

initialize_session_state()

if "discount_key" not in st.session_state:
    st.session_state.discount_key = 0

# =========================================================
# APP TITLE
# =========================================================

st.title("🐾 FacturaVET")

st.caption(
    "Stripe processes payments securely • IVA handled internally"
)

# =========================================================
# INVOICE TYPE
# =========================================================

invoice_type = st.radio(
    "Invoice type",
    [
        "B2C • Factura simplificada",
        "B2C • Factura completa",
        "B2B • Profesional con IRPF"
    ],
    horizontal=False,
    disabled=len(st.session_state.invoice_items) > 0
)

(
    requires_client_details,
    is_b2b,
    is_simplified_invoice
) = get_invoice_type_flags(
    invoice_type
)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📄 Invoice Info")

    invoice_number = st.text_input(
        "Invoice number",
        key=f"invoice_number_{st.session_state.form_key}",
        placeholder="e.g. 2026-001",
        value=""
    )

    # -----------------------------------------------------
    # FECHA DE EMISIÓN
    # -----------------------------------------------------

    invoice_date = date.today()

    st.date_input(
        "Fecha de emisión",
        value=invoice_date,
        disabled=True
    )

    st.session_state.invoice_date = invoice_date

    # -----------------------------------------------------
    # FECHA DE OPERACIÓN
    # -----------------------------------------------------

    show_operation_date = (
        invoice_type != "B2C • Factura simplificada"
    )

    if show_operation_date:

        operation_date = st.date_input(
            "Fecha de operación",
            key=f"operation_date_{st.session_state.form_key}",
            value=invoice_date,
            help=(
                "Only change if the service "
                "was performed on a different day"
            )
        )

    else:

        operation_date = invoice_date

    st.session_state.operation_date = operation_date

    # -----------------------------------------------------
    # SAVE INVOICE NUMBER
    # -----------------------------------------------------

    st.session_state.invoice_number = invoice_number

    if invoice_number:

        st.success(
            f"Invoice #{invoice_number}"
        )

    else:

        st.warning(
            "⚠️ Enter invoice number"
        )



# =========================================================
# CLIENT DETAILS - VERSIÓN NUEVA (flexible)
# =========================================================

    if requires_client_details:
        st.divider()
        st.subheader("👤 Datos del cliente")
        
        from config.client_fields import CLIENT_FIELDS, get_fields_by_section, get_full_address, validate_client
        
        # Opción: mostrar campos por secciones
        sections = ["basic", "address", "contact", "other"]
        
        for section in sections:
            section_fields = get_fields_by_section(section)
            if section_fields:
                # Título de sección
                if section == "basic":
                    st.markdown("**📋 Información básica**")
                elif section == "address":
                    st.markdown("**📍 Dirección**")
                elif section == "contact":
                    st.markdown("**📞 Contacto**")
                elif section == "other":
                    st.markdown("**📝 Información adicional**")
                
                # Mostrar campos de esta sección
                for field_name in section_fields:
                    field_config = CLIENT_FIELDS[field_name]
                    
                    # Obtener valor actual del session_state
                    current_value = st.session_state.client.get(field_name, "")
                    
                    # Usar valor por defecto si existe y el campo está vacío
                    if not current_value and "default" in field_config:
                        current_value = field_config["default"]
                    
                    # Mostrar según tipo de input
                    if field_config["input_type"] == "textarea":
                        value = st.text_area(
                            field_config["label"],
                            value=current_value,
                            key=f"client_{field_name}_{st.session_state.form_key}",
                            placeholder=field_config.get("placeholder", ""),
                            help=field_config.get("help", "")
                        )
                    else:
                        value = st.text_input(
                            field_config["label"],
                            value=current_value,
                            key=f"client_{field_name}_{st.session_state.form_key}",
                            placeholder=field_config.get("placeholder", ""),
                            help=field_config.get("help", "")
                        )
                    
                    # Guardar en el diccionario client
                    st.session_state.client[field_name] = value
                
                st.write("")  # espacio entre secciones
        
        # Mostrar dirección completa generada (feedback visual)
        full_address = get_full_address(st.session_state.client)
        if full_address:
            st.caption(f"📮 Dirección completa: {full_address}")
        
        # Validación en tiempo real (opcional)
        validation_error = validate_client(st.session_state.client)
        if validation_error:
            st.warning(validation_error)
        else:
            st.success("✅ Datos de cliente correctos")

# =========================================================
# ADD PRODUCT / SERVICE
# =========================================================

st.subheader("➕ Add service or product")

# =========================================================
# OPTIONAL DISCOUNT
# =========================================================

with st.expander("💸 Optional discount"):

    discount_type = st.selectbox(
        "Discount type",
        [
            "No discount",
            "Percentage (%)",
            "Fixed amount (€)"
        ],
        key=f"discount_type_{st.session_state.discount_key}"
    )

    if discount_type == "Percentage (%)":

        discount_value = st.number_input(
            "Discount %",
            min_value=0.0,
            max_value=100.0,
            step=5.0,
            format="%.1f",
            key=f"discount_value_{st.session_state.discount_key}"
        )

    elif discount_type == "Fixed amount (€)":

        discount_value = st.number_input(
            "Discount amount (€)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
            key=f"discount_value_{st.session_state.discount_key}"
        )

    else:

        discount_value = 0.0

# =========================================================
# PRODUCT FORM
# =========================================================

with st.form("add_product", clear_on_submit=True):

    name_input = st.text_input(
        "Description",
        placeholder="e.g. Ophthalmology consultation"
    )

    col1, col2 = st.columns(2)

    with col1:

        base_price = st.number_input(
            "Base price (€ IVA included)",
            min_value=0.0,
            step=1.0,
            format="%.2f"
        )

    with col2:

        if is_b2b:

            vat = st.radio(
                "IVA Rate",
                ["21%", "10%"],
                index=0,
                horizontal=True,
                disabled=True
            )

            st.caption(
                "🔒 B2B professional invoices use 21% IVA"
            )

        else:

            vat = st.radio(
                "IVA Rate",
                ["21%", "10%"],
                horizontal=True
            )

    submitted = st.form_submit_button(
        "Add to invoice",
        use_container_width=True
    )

    # -----------------------------------------------------
    # PROCESS ITEM (FIXED PARAMETER NAMES)
    # -----------------------------------------------------

    if submitted and name_input.strip() != "":

        item = calculate_invoice_item(
            name=name_input,
            base_price_gross=base_price,
            vat=vat,
            discount_type=discount_type,
            discount_value_input=discount_value
        )

        st.session_state.invoice_items.append(item)
        st.session_state.discount_key += 1

        st.rerun()

# =========================================================
# CURRENT INVOICE
# =========================================================

if st.session_state.invoice_items:

    st.divider()

    st.subheader("📋 Current invoice")

    totals = calculate_totals(
        st.session_state.invoice_items
    )

    total_gross = totals["total_gross"]
    total_net = totals["total_net"]
    total_vat_21 = totals["total_vat_21"]
    total_vat_10 = totals["total_vat_10"]
    total_vat = totals["total_vat"]

    # -----------------------------------------------------
    # DISPLAY ITEMS (Fixed Columns showing detailed IVA values)
    # -----------------------------------------------------
    
    # Clean Table Headers
    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3, 1.4, 1.6, 1.4, 0.6])
    with col_h1: st.markdown("**Concepto**")
    with col_h2: st.markdown("**Base (Neto)**")
    with col_h3: st.markdown("**Cuota IVA**")
    with col_h4: st.markdown("**Total (Bruto)**")
    with col_h5: st.write("") # Delete button space
    st.write("")

    for idx, item in enumerate(st.session_state.invoice_items, 1):
        col1, col2, col3, col4, col5 = st.columns([3, 1.4, 1.6, 1.4, 0.6])

        with col1:
            st.write(f"{idx}. {item['name']}")

        with col2:
            st.write(f"{item['net_price']:.2f} €")

        with col3:
            # 💡 Displays both the percentage rate and the exact Euro tax value!
            st.write(f"{item['vat']} ({item['vat_amount']:.2f} €)")

        with col4:
            st.write(f"{item['gross_price']:.2f} €")
            if item["discount_amount"] > 0:
                st.caption(f"Desc: -{item['discount_amount']:.2f} €")

        with col5:
            if st.button("❌", key=f"delete_{idx}"):
                st.session_state.invoice_items.pop(idx - 1)
                st.rerun()

    # =====================================================
    # IRPF
    # =====================================================

    irpf_data = calculate_irpf(
        total_gross,
        total_net,
        is_b2b
    )

    irpf_total = irpf_data["irpf_total"]

    final_payable = irpf_data["final_payable"]

    invoice_data = build_invoice_object(
        session_state=st.session_state,
        invoice_type=invoice_type,
        invoice_items=st.session_state.invoice_items,
        totals=totals,
        irpf_data=irpf_data,
        username=username,
        is_b2b=is_b2b
    )

    # =====================================================
    # TOTAL DISPLAY
    # =====================================================

    st.divider()

    st.markdown(
    
        build_total_title(
            is_b2b,
            final_payable,
            total_gross
        )
    )
    
    st.caption(
    
        build_total_caption(
            is_b2b,
            total_net,
            total_vat_21,
            total_vat_10,
            irpf_total
        )
    )

    # =====================================================
    # ACTION BUTTONS (VERSIÓN ACTUALIZADA)
    # =====================================================
    
    st.divider()
    st.subheader("📄 Gestión de Factura")
    
    # Mostrar estado actual (opcional)
    st.info(f"**Estado:** {st.session_state.invoice_status}")
    
    # =====================================================
    # FILA 1: ACCIONES DE PDF
    # =====================================================
    
    col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 1, 2])
    
    with col_pdf1:
        if st.button("📄 Generar PDF", type="primary", use_container_width=True):
            from invoice_engine.pdf_service import generate_pdf
            from invoice_engine.invoice_service import validate_invoice
            from config.client_fields import validate_client
            
            # Validar datos obligatorios
            error = validate_invoice(
                invoice_number=st.session_state.invoice_number,
                invoice_items=st.session_state.invoice_items,
                requires_client_details=requires_client_details,
                client_data=st.session_state.client
            )
            
            if error:
                st.error(error)
            else:
                with st.spinner("Generando PDF..."):
                    # Reconstruir invoice_data con datos actuales
                    invoice_data = build_invoice_object(
                        session_state=st.session_state,
                        invoice_type=invoice_type,
                        invoice_items=st.session_state.invoice_items,
                        totals=totals,
                        irpf_data=irpf_data,
                        username=username,
                        is_b2b=is_b2b
                    )
                    
                    pdf_bytes = generate_pdf(invoice_data)
                    st.session_state.generated_pdf = pdf_bytes
                    st.session_state.invoice_status = "READY_FOR_VALIDATION"
                    st.success("✅ PDF generado correctamente")
                    st.rerun()
    
    with col_pdf2:
        if st.session_state.get("generated_pdf"):
            st.download_button(
                label="💾 Descargar PDF",
                data=st.session_state.generated_pdf,
                file_name=f"factura_{st.session_state.invoice_number}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.button("💾 Sin PDF", disabled=True, use_container_width=True)
    
    with col_pdf3:
        st.caption("Genera el PDF antes de enviar la factura al cliente")
    
    # =====================================================
    # FILA 2: BOTONES EXISTENTES (Stripe, etc.)
    # =====================================================
    
    col1, col2, col3 = st.columns(3)
    
    # -----------------------------------------------------
    # GENERATE STRIPE LINK
    # -----------------------------------------------------
    with col1:
        if st.session_state.invoice_status != "DRAFT":
            if st.button("🚀 Generate Stripe link", type="primary", use_container_width=True):
                validation_error = validate_invoice(
                    invoice_number=st.session_state.invoice_number,
                    invoice_items=st.session_state.invoice_items
                )
            
                if validation_error:
                
                    st.error(validation_error)
                
                else:
                
                    payable_items = get_payable_items(
                        st.session_state.invoice_items
                    )
                
                    with st.spinner(
                        "Creating Stripe payment link..."
                    ):
    
                        try:
    
                            line_items = build_line_items(
                                payable_items=payable_items,
                                is_b2b=is_b2b,
                                final_payable=final_payable,
                                invoice_number=st.session_state.invoice_number
                            )
                    
                            metadata = build_metadata(
                                session_state=st.session_state,
                                total_gross=total_gross,
                                total_net=total_net,
                                total_vat=total_vat,
                                irpf_total=irpf_total,
                                final_payable=final_payable,
                                username=username
                            )
                    
                            checkout_session = create_checkout_session(
                                line_items=line_items,
                                metadata=metadata
                            )
                    
                            st.success(
                                f"✅ Payment link ready "
                                f"for Invoice "
                                f"#{st.session_state.invoice_number}"
                            )
                        
                            if is_b2b:
                        
                                st.info(
                                    f"Company will pay "
                                    f"€{final_payable:.2f}"
                                )
                        
                            else:
                        
                                st.info(
                                    f"Client will pay "
                                    f"€{total_gross:.2f}"
                                )
                        
                            st.markdown(
                                "**Send this secure payment "
                                "link to your client:**"
                            )
                        
                            st.code(
                                checkout_session.url,
                                language="text"
                            )
                        
                        except Exception as e:
                        
                            st.error(
                                f"Stripe error: {str(e)}"
                            )
                    pass
            else:
                st.button("🚀 Generar PDF primero", disabled=True, use_container_width=True)
    
    # -----------------------------------------------------
    # START NEW INVOICE
    # -----------------------------------------------------
    with col2:
        if st.button("🔄 Start new invoice", use_container_width=True):
            st.session_state.invoice_items = []
            st.session_state.generated_pdf = None
            st.session_state.invoice_status = "DRAFT"
            st.session_state.form_key += 1
            st.rerun()
    
    # -----------------------------------------------------
    # CLEAR ALL ITEMS
    # -----------------------------------------------------
    with col3:
        if st.button("🗑 Clear all items", use_container_width=True):
            st.session_state.invoice_items = []
            st.session_state.generated_pdf = None
            st.session_state.invoice_status = "DRAFT"
            st.rerun()

# =========================================================
# EMPTY STATE
# =========================================================

else:

    st.info(
        "💡 Add your first product or service above"
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🔐 Stripe securely processes card, "
    "Apple Pay, Google Pay and Bizum payments"
)

st.caption(
    "📝 Prices entered already include IVA • "
    "Stripe is used only as payment processor"
)
