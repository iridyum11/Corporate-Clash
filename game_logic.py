def resolve_combat(attacker_card, defender_card):
    """
    Calculates the outcome of a combat encounter, including damage and recoil.
    Returns the damage to the defender, damage to the attacker (recoil), and a log message.
    """
    multiplier = 1.0
    is_critical = False

    # Check Rock-Paper-Scissors Logic
    advantages = {
        "IT Support": "Management",
        "Management": "Sales",
        "Sales": "HR",
        "HR": "IT Support"
    }

    if advantages.get(attacker_card['class']) == defender_card['class']:
        multiplier = 2.0
        is_critical = True

    damage_to_defender = attacker_card['attack'] * multiplier

    # Determine outcome and log message
    if damage_to_defender < defender_card['defense']:
        # Attack fails, defender retaliates
        damage_to_attacker = defender_card['attack']
        log_message = f"{attacker_card['name']}'s attack fails! {defender_card['name']} retaliates, dealing {damage_to_attacker} recoil damage."
        if is_critical:
            log_message = f"A CRITICAL attack from {attacker_card['name']} was not enough! " + log_message
    else:
        # Attack succeeds
        damage_to_attacker = 0
        log_message = f"{attacker_card['name']} attacks {defender_card['name']}, dealing {damage_to_defender} damage!"
        if is_critical:
            log_message = f"CRITICAL HIT! {log_message}"

    return damage_to_defender, damage_to_attacker, log_message
