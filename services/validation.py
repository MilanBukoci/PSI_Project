def validate_package(x, y, z, weight):
    try:
        x, y, z = int(x), int(y), int(z)
        weight = float(weight)
    except ValueError:
        return "Zadajte platné čísla"
    if any(v <= 0 or v > 300 for v in [x, y, z]):
        return "Rozmery musia byť medzi 1 a 300 cm"
    if weight <= 0 or weight > 100:
        return "Hmotnosť musí byť medzi 1 a 100 kg"
    return None