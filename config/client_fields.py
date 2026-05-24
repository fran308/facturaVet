# client_fields.py
"""
Configuración central de los campos del cliente.
MODIFICA SOLO ESTE ARCHIVO para cambiar los campos del cliente.
"""

CLIENT_FIELDS = {
    # Campo interno: (configuración)
    "name": {
        "label": "Nombre / Razón social",
        "input_type": "text",
        "required": True,
        "help": "Nombre completo de la persona o empresa",
        "placeholder": "Ej: Clínica Veterinaria López",
        "section": "basic"  # para agrupar visualmente
    },
    "nif": {
        "label": "NIF / CIF",
        "input_type": "text",
        "required": True,
        "help": "Identificación fiscal (DNI, NIF, CIF, NIE)",
        "placeholder": "Ej: B12345678",
        "section": "basic"
    },
    "street": {
        "label": "Calle",
        "input_type": "text",
        "required": False,
        "help": "Nombre de la calle",
        "placeholder": "Ej: Avenida de la Constitución",
        "section": "address"
    },
    "street_number": {
        "label": "Número",
        "input_type": "text",
        "required": False,
        "help": "Número de portal, piso, etc",
        "placeholder": "Ej: 42, 3ºA",
        "section": "address"
    },
    "city": {
        "label": "Municipio",
        "input_type": "text",
        "required": False,
        "help": "Ciudad o municipio",
        "placeholder": "Ej: Madrid",
        "section": "address"
    },
    "postal_code": {
        "label": "Código Postal",
        "input_type": "text",
        "required": False,
        "help": "Código postal (5 dígitos)",
        "placeholder": "Ej: 28001",
        "section": "address"
    },
    "province": {
        "label": "Provincia",
        "input_type": "text",
        "required": False,
        "help": "Provincia",
        "placeholder": "Ej: Madrid",
        "section": "address"
    },
    "country": {
        "label": "País",
        "input_type": "text",
        "required": False,
        "help": "País",
        "placeholder": "Ej: España",
        "default": "España",
        "section": "address"
    },
    "phone": {
        "label": "Teléfono",
        "input_type": "text",
        "required": False,
        "help": "Teléfono de contacto",
        "placeholder": "Ej: 600 123 456",
        "section": "contact"
    },
    "email": {
        "label": "Email",
        "input_type": "text",
        "required": False,
        "help": "Correo electrónico",
        "placeholder": "Ej: cliente@ejemplo.com",
        "section": "contact"
    },
    "notes": {
        "label": "Notas",
        "input_type": "textarea",
        "required": False,
        "help": "Información adicional",
        "placeholder": "Cualquier observación relevante",
        "section": "other"
    }
}


def get_required_fields():
    """Devuelve lista de campos obligatorios (para validación)"""
    return [field for field, config in CLIENT_FIELDS.items() if config.get("required", False)]


def get_field_label(field_name):
    """Devuelve la etiqueta de un campo"""
    return CLIENT_FIELDS.get(field_name, {}).get("label", field_name)


def get_fields_by_section(section):
    """Devuelve campos de una sección específica"""
    return [
        field for field, config in CLIENT_FIELDS.items() 
        if config.get("section") == section
    ]


def get_all_sections():
    """Devuelve todas las secciones disponibles"""
    sections = set(config.get("section", "basic") for config in CLIENT_FIELDS.values())
    return sorted(list(sections))


def get_full_address(client_data):
    """Construye dirección completa a partir de campos individuales"""
    parts = []
    
    # Calle y número
    if client_data.get("street"):
        street = client_data["street"]
        if client_data.get("street_number"):
            street += f", {client_data['street_number']}"
        parts.append(street)
    
    # Código postal + ciudad
    if client_data.get("postal_code") or client_data.get("city"):
        city_part = ""
        if client_data.get("postal_code"):
            city_part += client_data["postal_code"]
        if client_data.get("city"):
            if city_part:
                city_part += " "
            city_part += client_data["city"]
        if city_part:
            parts.append(city_part)
    
    # Provincia
    if client_data.get("province"):
        parts.append(client_data["province"])
    
    # País (solo si no es España o si está explícitamente puesto)
    if client_data.get("country") and client_data["country"] not in ["", "España"]:
        parts.append(client_data["country"])
    
    return ", ".join(parts)


def validate_client(client_data):
    """Valida que todos los campos obligatorios estén presentes"""
    missing = []
    for required_field in get_required_fields():
        value = client_data.get(required_field, "")
        if not value or not value.strip():
            missing.append(get_field_label(required_field))
    
    if missing:
        return f"❌ Faltan campos obligatorios: {', '.join(missing)}"
    return None
