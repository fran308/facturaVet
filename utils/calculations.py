#utils/calculations.py

from decimal import Decimal, ROUND_HALF_UP

# Constantes Decimal para evitar imprecisiones
TWO_PLACES = Decimal('0.01')
THREE_PLACES = Decimal('0.001')  # Para operaciones intermedias
C_100 = Decimal('100')
C_15 = Decimal('0.15')
C_21 = Decimal('0.21')
C_10 = Decimal('0.10')
C_1 = Decimal('1')

def to_decimal(value) -> Decimal:
    """Convierte cualquier entrada de forma segura a Decimal."""
    if value is None:
        return Decimal('0.00')
    # Manejar strings con comas
    if isinstance(value, str):
        value = value.replace(',', '.')
    return Decimal(str(value))

def round_currency(value) -> float:
    """Redondea un valor al método fiscal español (ROUND_HALF_UP) y retorna float."""
    dec = to_decimal(value)
    return float(dec.quantize(TWO_PLACES, rounding=ROUND_HALF_UP))

def round_intermediate(value) -> Decimal:
    """
    Redondeo intermedio a 3 decimales según normativa.
    Importante: Los cálculos de IVA se hacen con 3 decimales antes del redondeo final.
    """
    dec = to_decimal(value)
    return dec.quantize(THREE_PLACES, rounding=ROUND_HALF_UP)

def calculate_discount(base_price: Decimal, discount_type: str, discount_value: Decimal) -> Decimal:
    """Calcula el monto del descuento usando Decimal sin redondear prematuramente."""
    if discount_type == "Percentage (%)":
        return base_price * (discount_value / C_100)
    elif discount_type == "Fixed amount (€)":
        return discount_value
    return Decimal('0.00')

def calculate_invoice_item(name: str, base_price_gross, vat: str, discount_type: str, discount_value_input):
    """
    Crea un item de factura con cálculos basados en precisión Decimal.
    
    CORREGIDO: Ahora cumple con la normativa española:
    1. Calcula base imponible con 3 decimales
    2. Redondea base imponible a 2 decimales
    3. Calcula IVA sobre base redondeada
    4. Redondea IVA a 2 decimales
    """
    
    # 1. Convertir entradas a Decimal de alta precisión
    b_price_gross = to_decimal(base_price_gross)
    disc_value = to_decimal(discount_value_input)
    
    # Determinar tipo de IVA
    if vat == "21%":
        vat_rate = C_21
    elif vat == "10%":
        vat_rate = C_10
    else:
        vat_rate = Decimal('0.00')
    
    # 2. Calcular descuento y precio bruto final (CON IVA incluido)
    discount_amount = calculate_discount(b_price_gross, discount_type, disc_value)
    final_gross_price = max(b_price_gross - discount_amount, Decimal('0.00'))
    
    # 3. Calcular base imponible (SIN IVA) - CRÍTICO: Redondeo intermedio a 3 decimales
    # Fórmula: Neto = Bruto / (1 + Tipo IVA)
    net_price_exact = final_gross_price / (C_1 + vat_rate)
    
    # 🔑 CLAVE: Redondear la base imponible a 3 decimales (normativa)
    net_price_rounded_3d = net_price_exact.quantize(THREE_PLACES, rounding=ROUND_HALF_UP)
    
    # 4. Calcular IVA sobre la base imponible (con 3 decimales)
    vat_amount_exact = net_price_rounded_3d * vat_rate
    
    # 5. Redondear BASE e IVA a 2 decimales para la factura
    net_price_final = net_price_rounded_3d.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    vat_amount_final = vat_amount_exact.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    
    # Verificar consistencia: Precio final = Base + IVA (redondeados)
    final_price_check = net_price_final + vat_amount_final
    
    # Si hay diferencia de 1 céntimo por redondeo, ajustamos el IVA
    if final_price_check != final_gross_price.quantize(TWO_PLACES, rounding=ROUND_HALF_UP):
        # Ajuste fino: la diferencia debe ser de 1 céntimo como máximo
        difference = final_gross_price.quantize(TWO_PLACES, rounding=ROUND_HALF_UP) - final_price_check
        if abs(difference) == Decimal('0.01'):
            vat_amount_final += difference
    
    return {
        "name": name.strip(),
        "base_price": round_currency(b_price_gross),
        "discount_type": discount_type,
        "discount_value": round_currency(disc_value),
        "discount_amount": round_currency(discount_amount),
        "gross_price": round_currency(final_gross_price),
        "net_price": round_currency(net_price_final),
        "vat": vat,
        "vat_rate": float(vat_rate),
        "vat_amount": round_currency(vat_amount_final),
        # Guardamos los Decimal originales para totales perfectos
        "_net_exact": net_price_final,
        "_vat_exact": vat_amount_final,
        "_gross_exact": final_gross_price
    }

def calculate_totals(invoice_items):
    """
    Calcula los totales acumulando los valores exactos antes de redondear.
    IMPORTANTE: Los totales se calculan sumando valores REDONDEADOS (no exactos)
    para cumplir con la normativa de Hacienda.
    """
    total_gross = Decimal('0.00')
    total_net = Decimal('0.00')
    total_vat_21 = Decimal('0.00')
    total_vat_10 = Decimal('0.00')
    
    for item in invoice_items:
        # Sumamos los valores ya redondeados (como aparecen en factura)
        total_gross += to_decimal(item.get("_gross_exact", item["gross_price"]))
        total_net += to_decimal(item.get("_net_exact", item["net_price"]))
        
        item_vat = to_decimal(item.get("_vat_exact", item["vat_amount"]))
        if item["vat"] == "21%":
            total_vat_21 += item_vat
        else:
            total_vat_10 += item_vat
    
    # Redondear totales finales a 2 decimales
    total_vat = total_vat_21 + total_vat_10
    
    return {
        "total_gross": round_currency(total_gross),
        "total_net": round_currency(total_net),
        "total_vat_21": round_currency(total_vat_21),
        "total_vat_10": round_currency(total_vat_10),
        "total_vat": round_currency(total_vat)
    }

def calculate_irpf(total_gross, total_net, is_b2b: bool):
    """
    Calcula el IRPF (15%) sobre la base imponible final.
    CORREGIDO: El IRPF se calcula sobre la base imponible redondeada.
    """
    t_net = to_decimal(total_net)
    t_gross = to_decimal(total_gross)
    
    irpf_total = Decimal('0.00')
    final_payable = t_gross
    
    if is_b2b:
        # IRPF se calcula sobre la base imponible REDONDEADA
        irpf_total = t_net * C_15
        # Redondear IRPF a 2 decimales
        irpf_total = irpf_total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        final_payable = t_gross - irpf_total
    
    return {
        "irpf_total": round_currency(irpf_total),
        "final_payable": round_currency(final_payable)
    }


# Función adicional para validar facturas
def validate_invoice_consistency(invoice_items, totals):
    """
    Valida que la suma de líneas coincide con los totales.
    Útil para depuración y compliance.
    """
    sum_net = Decimal('0.00')
    sum_vat = Decimal('0.00')
    sum_gross = Decimal('0.00')
    
    for item in invoice_items:
        sum_net += to_decimal(item.get("_net_exact", item["net_price"]))
        sum_vat += to_decimal(item.get("_vat_exact", item["vat_amount"]))
        sum_gross += to_decimal(item.get("_gross_exact", item["gross_price"]))
    
    return {
        "consistent": (round_currency(sum_net) == totals["total_net"] and
                      round_currency(sum_vat) == totals["total_vat"] and
                      round_currency(sum_gross) == totals["total_gross"]),
        "diff_net": round_currency(sum_net - totals["total_net"]),
        "diff_vat": round_currency(sum_vat - totals["total_vat"]),
        "diff_gross": round_currency(sum_gross - totals["total_gross"])
    }
