from decimal import Decimal, ROUND_HALF_UP

# Constantes Decimal para evitar imprecisiones
TWO_PLACES = Decimal('0.01')
C_100 = Decimal('100')
C_15 = Decimal('0.15')

def to_decimal(value) -> Decimal:
    """Convierte cualquier entrada de forma segura a Decimal."""
    if value is None:
        return Decimal('0.00')
    return Decimal(str(value))

def round_currency(value) -> float:
    """Redondea un valor al método fiscal español (ROUND_HALF_UP) y retorna float."""
    dec = to_decimal(value)
    return float(dec.quantize(TWO_PLACES, rounding=ROUND_HALF_UP))

def calculate_discount(base_price: Decimal, discount_type: str, discount_value: Decimal) -> Decimal:
    """Calcula el monto del descuento usando Decimal sin redondear prematuramente."""
    if discount_type == "Percentage (%)":
        return base_price * (discount_value / C_100)
    elif discount_type == "Fixed amount (€)":
        return discount_value
    return Decimal('0.00')

def calculate_invoice_item(name: str, base_price_gross, vat: str, discount_type: str, discount_value_input):
    """Crea un item de factura con cálculos basados en precisión Decimal."""
    
    # 1. Convertir entradas a Decimal de alta precisión
    b_price_gross = to_decimal(base_price_gross)
    disc_value = to_decimal(discount_value_input)
    vat_rate = Decimal('0.21') if vat == "21%" else Decimal('0.10')
    
    # 2. Calcular descuento y precio bruto final (con IVA)
    discount_amount = calculate_discount(b_price_gross, discount_type, disc_value)
    final_gross_price = max(b_price_gross - discount_amount, Decimal('0.00'))
    
    # 3. Desglose inverso EXACTO: Encontrar la Base Imponible antes de redondear
    # Fórmula: Neto = Bruto / (1 + Tipo IVA)
    net_price_exact = final_gross_price / (Decimal('1') + vat_rate)
    
    # 4. El IVA se calcula aplicando el porcentaje sobre la base exacta, NO por resta
    vat_amount_exact = net_price_exact * vat_rate
    
    # 5. Redondear de manera individual para la presentación de la línea
    return {
        "name": name.strip(),
        "base_price": round_currency(b_price_gross),
        "discount_type": discount_type,
        "discount_value": round_currency(disc_value),
        "discount_amount": round_currency(discount_amount),
        "gross_price": round_currency(final_gross_price),
        "net_price": round_currency(net_price_exact),
        "vat": vat,
        "vat_rate": float(vat_rate),
        "vat_amount": round_currency(vat_amount_exact),
        # Guardamos los Decimal originales para que el cálculo de totales sea perfecto
        "_net_exact": net_price_exact,
        "_vat_exact": vat_amount_exact,
        "_gross_exact": final_gross_price
    }

def calculate_totals(invoice_items):
    """Calcula los totales acumulando los valores exactos antes de redondear."""
    total_gross_exact = Decimal('0.00')
    total_net_exact = Decimal('0.00')
    total_vat_21_exact = Decimal('0.00')
    total_vat_10_exact = Decimal('0.00')
    
    for item in invoice_items:
        # Recuperamos el valor exacto (o lo convertimos si viene de una fuente externa)
        total_gross_exact += to_decimal(item.get("_gross_exact", item["gross_price"]))
        total_net_exact += to_decimal(item.get("_net_exact", item["net_price"]))
        
        item_vat_exact = to_decimal(item.get("_vat_exact", item["vat_amount"]))
        if item["vat"] == "21%":
            total_vat_21_exact += item_vat_exact
        else:
            total_vat_10_exact += item_vat_exact
            
    total_vat_exact = total_vat_21_exact + total_vat_10_exact
    
    return {
        "total_gross": round_currency(total_gross_exact),
        "total_net": round_currency(total_net_exact),
        "total_vat_21": round_currency(total_vat_21_exact),
        "total_vat_10": round_currency(total_vat_10_exact),
        "total_vat": round_currency(total_vat_exact)
    }

def calculate_irpf(total_gross, total_net, is_b2b: bool):
    """Calcula el IRPF (15%) sobre la base imponible final."""
    t_gross = to_decimal(total_gross)
    t_net = to_decimal(total_net)
    
    irpf_total = Decimal('0.00')
    final_payable = t_gross
    
    if is_b2b:
        irpf_total = t_net * C_15
        final_payable = t_gross - irpf_total
        
    return {
        "irpf_total": round_currency(irpf_total),
        "final_payable": round_currency(final_payable)
    }
