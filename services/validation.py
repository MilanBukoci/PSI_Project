def validate_package(x, y, z, weight):
    # Pokus o konverziu vstupov — vráti chybu ak nie sú čísla
    try:
        x, y, z = int(x), int(y), int(z)
        weight = float(weight)
    except ValueError:
        return "Zadajte platné čísla"

    # Každý rozmer musí byť v rozsahu 1–300 cm
    if any(v <= 0 or v > 300 for v in [x, y, z]):
        return "Rozmery musia byť medzi 1 a 300 cm"

    # Hmotnosť obmedzená na 1–100 kg
    if weight <= 0 or weight > 100:
        return "Hmotnosť musí byť medzi 1 a 100 kg"

    return None