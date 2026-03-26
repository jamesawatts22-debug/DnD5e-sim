import random
import re
from core.combat.combat_engine import CombatEngine

def simulate_combat():
    attacker = {
        "proficiency_bonus": 2,
        "weapon_bonus": 3,
        "damage_die": 6,
        "on_hit_effect": "lifesteal"
    }

    target = {
        "ac": 12
    }

    result = CombatEngine.resolve_attack(attacker, target)
    return result