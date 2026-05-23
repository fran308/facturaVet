# Complete Working Solution: Streamlit + Stripe for Spanish Veterinary Clinic

## Problem Solved
Mobile-friendly payment link generator that:
- Accepts manual invoice numbers (no automatic numbering)
- Handles Spanish VAT (21% and 10%) correctly
- User enters **price including VAT** (e.g., €50 including 21% VAT)
- Stripe charges the correct gross amount and splits net + VAT automatically


---

# 🐾 FacturaVET — Ojo Veterinario

Secure, cloud-ready billing portal and payment link generator custom-built for veterinary ophthalmology inter-consultations, clinical diagnostics, and direct pet care services.

---

## 🚀 Architecture Overview

This software acts as a specialized administrative layout. It uses **Stripe** as a "dumb" payment processor (capturing strictly transaction tokens) while managing precise fiscal rounding regulations and multi-rate tax structures (**IVA 21% / 10%** and **IRPF -15%**) completely internally. 

The application is built on top of **Streamlit** for a lightweight field-ready UI, and utilizes **ReportLab** for native PDF rendering that adheres strictly to Spanish invoicing regulations (*Reglamento de Facturación*).

[UI Client Data Form] ──► [Decimal Math Engine] ──► [3rd Party Pre-Flight API]
│
[Stripe Link Generated] ◄── [Render Legal 5-Col PDF] ◄────┴─ (If Cleared)

---

## 📂 File Directory Descriptions

### 🎛️ Root Directory
* **`app.py`**: The main entry point of the application. Routes user authentication (`streamlit-authenticator`), UI state updates, item forms, and execution loops.
* **`requirements.txt`**: Pinned external dependencies required to compile the runtime container on Streamlit Cloud.

### ⚙️ `config/` (Configuration & State)
* **`company_config.py`**: Stores public branding styling profiles (Ojo Veterinario corporate purple `#a747a2`), banking registries (IBAN/BIC), and text layout footer templates.
* **`client_fields.py`**: Defines layout field schemas used to dynamically toggle between *Facturas Simplificadas* and full B2B customer sheets.
* **`session_state.py`**: Instantiates global reactive dictionaries to protect data integrity across form submission refreshes.

### 🔌 `services/` (Data Pipelines & Connectors)
* **`stripe_service.py`**: Translates local invoice metadata arrays into single-use Stripe Checkout session payloads.
* **`pdf_service.py`**: Strict 5-column ReportLab document engine that maps *Base Imponible*, *Tipo IVA*, *Cuota IVA*, and *Importe Total* for every item row. Contains commented structure placeholders for future *Verifactu* QR clearance layouts.
* **`invoice_builder.py`**: Acts as an object assembler, structuring raw state variables into uniform dictionary packages for the PDF compiler.

### 🧮 `utils/` (Logic & Internal UI Helpers)
* **`calculations.py`**: High-precision math engine utilizing Python's `Decimal` module and `ROUND_HALF_UP` configurations to prevent penny rounding drift during reverse-tax breakdowns.
* **`invoice_service.py`**: Validates structural fields, tracks transaction values, and formats contextual UI subheadings.
* **`helpers.py`**: Secondary utility functions for text manipulation and date conversions.
* **`styles.py`**: Handles raw CSS style injections to format backgrounds and isolate active input sections.

---

## 🇪🇸 Fiscal Compliance Architecture

To maintain bulletproof alignment with current tax standards, the application enforces the following automated behaviors:
1. **Ununified Desglose:** The itemized grids split the exact Euro tax amount (*Cuota IVA*) cell-by-cell instead of applying blanket approximations to the subtotal block.
2. **Dynamic Data Shifting:** Toggling a *Factura Simplificada* automatically purges client identification parameters from the header metadata layout to maintain strict customer data privacy baselines.
3. **Spanish Standard Date Alignment:** All transactional document sheets intercept standard calendar timestamps and format them explicitly into standard `dd/mm/yyyy` text metrics.

---

## 🔐 Environmental Secrets Configuration

To run this platform securely on Streamlit Cloud, the following structured fields must be populated inside your private **Secrets** management panel (`secrets.toml`):

```toml
STRIPE_SECRET_KEY = "sk_live_..."
cookie_name = "facturavet_cookie"
cookie_key = "your_secret_cookie_hash_key"
cookie_expiry_days = 30

[usernames.A]
email = "john@doe.es"
name = "A"
password = "your_hashed_password"

[usernames.B]
email = "jane@doe.es"
name = "B"
password = "your_hashed_password"

[company]
legal_name = "xxxxx"
trading_name = "xxxxx"
nif = "2xxxxx"
specialty = "xxxxx"

[company.address]
street = "xxxx"
street_number = "xxxxxxx"
postal_code = "postal code"
city = "xxxxxxxxxxxxx"
province = "xxxxxx"

[company.contact]
phone = "number"
email = "john@doe.es"

[company.bank]
name = "Your Bank Name"
bic = "XXXXXXXX"
iban = "ESXX00000000000000000000"

[company.payment_terms]
method = "transferencia"
days = 15
