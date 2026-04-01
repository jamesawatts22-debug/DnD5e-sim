import random
from .attack_roller import attack_roll, damage_roll

class CombatEngine:
    @staticmethod
    def resolve_attack(attacker, target, advantage=0):
        """
        Resolves a single attack from attacker to target.
        attacker: dict containing proficiency_bonus, weapon_bonus, damage_die, on_hit_effect, etc.
        target: dict containing ac.
        advantage: 1 for advantage, -1 for disadvantage, 0 for normal.
        """
        prof = int(attacker.get('proficiency_bonus', 0))
        w_bonus = int(attacker.get('weapon_bonus', 0))
        attack_bonus = prof + w_bonus
        
        target_ac = int(target.get('ac', 10))
        
        # Determine crit range
        crit_range = [20]
        if attacker.get('crit_on_18'):
            crit_range = [18, 19, 20]
        elif attacker.get('crit_on_19'):
            crit_range = [19, 20]

        res = attack_roll(attack_bonus, target_ac, crit_range=tuple(crit_range), advantage=advantage)
        
        damage = 0
        effects = []
        
        if res['hit']:
            damage = damage_roll(attacker.get('damage_die', 4), w_bonus, critical=res['critical'], player_data=attacker)
            
            # Handle standard on-hit effects
            effect_type = attacker.get('on_hit_effect', '').lower()
            if effect_type == 'vex':
                effects.append(('player_advantage', 1))
            elif effect_type == 'sap':
                effects.append(('enemy_advantage', -1))
            elif effect_type == 'poison':
                effects.append(('msg', "Poisoned!"))
                
            # Handle weapon enchantments
            enchant = attacker.get('weapon_enchantment')
            if enchant == 'lifesteal':
                heal_amt = max(1, damage // 2)
                effects.append(('heal_attacker', heal_amt))
            elif enchant == 'fire':
                fire_dmg = random.randint(1, 4)
                damage += fire_dmg
                effects.append(('msg', f"Fire deals +{fire_dmg} damage!"))
            elif enchant == 'frost':
                effects.append(('enemy_advantage', -1)) # Slow effect
                effects.append(('msg', "Frost chills the target!"))
            elif enchant == 'silence':
                # DC 12 Silence save
                from .attack_roller import roll_d20
                save_roll, _ = roll_d20()
                if save_roll < 12:
                    effects.append(('silence', 1))
                    effects.append(('msg', "Target is Silenced!"))
                else:
                    effects.append(('msg', "Target resisted Silence."))

        else:
            # Handle miss effects (like Graze)
            effect_type = attacker.get('on_hit_effect', '').lower()
            if effect_type == 'graze':
                graze_dmg = prof
                effects.append(('msg', f"Graze dealt {graze_dmg} damage"))
                damage = graze_dmg

        return {
            'hit': res['hit'],
            'damage': damage,
            'critical': res['critical'],
            'roll': res['roll'],
            'effects': effects
        }

    @staticmethod
    def resolve_ability(ability_data, caster, targets):
        """
        Resolves an ability (skill or spell) cast against one or more targets.
        targets: can be a single target dict or a list of target dicts.
        """
        from .attack_roller import roll_dice, roll_d20
        
        # Ensure targets is a list
        if not isinstance(targets, list):
            targets = [targets]
            
        is_aoe = ability_data.get('aoe', False)
        # If not AOE, we only hit the first target in the list
        active_targets = targets if is_aoe else [targets[0]]

        # Check 'cost' (skills) first, then 'level' (spells)
        mana_cost = ability_data.get('cost', ability_data.get('level', 0))
        
        total_damage = 0
        total_healing = 0
        all_effects = []
        msg_parts = []
        
        name = ability_data.get('name', 'Ability')
        resource_type = ability_data.get('resource', 'mp')
        
        if resource_type == 'sp':
            msg_parts.append(f"Using skill: {name}!")
        else:
            msg_parts.append(f"Casting spell: {name}...")

        spell_type = ability_data.get('type', 'attack')
        dice_str = ability_data.get('dice', '')
        
        # Multi-hit logic (like Fighter Extra Attack)
        iterations = int(caster.get('attack_count', 1)) if ability_data.get('use_attack_count') else 1
        
        hits_by_target = {id(t): 0 for t in active_targets}
        damage_by_target = {id(t): 0 for t in active_targets}

        for _ in range(iterations):
            for target in active_targets:
                # Sneak Attack Scaling
                current_dice = dice_str
                if ability_data.get('use_sneak_dice'):
                    num_dice = caster.get('sneak_attack_rolls', 1)
                    # multiplier for empowered skills
                    multiplier = ability_data.get('multiplier', 1)
                    current_dice = f"{num_dice * multiplier}d6"
                    w_bonus = caster.get('weapon_bonus', 0)
                    if w_bonus > 0:
                        current_dice += f"+{w_bonus}"
                
                # Simplified Success Logic
                if spell_type == "attack":
                    roll, _ = roll_d20()
                    if roll >= 6: # 75% hit chance
                        dmg = roll_dice(current_dice) if current_dice else 0
                        damage_by_target[id(target)] += dmg
                        hits_by_target[id(target)] += 1
                
                elif spell_type == "save":
                    roll, _ = roll_d20()
                    # Base success: roll >= 8 (65%)
                    # Each point of spell_save improves success by 5% (1 on d20)
                    spell_save_bonus = int(caster.get('spell_save', 0))
                    # Cap spell_save at 5
                    spell_save_bonus = min(5, spell_save_bonus)
                    
                    target_roll = max(3, 8 - spell_save_bonus) # Cap at 90% success (roll >= 3)
                    
                    if roll >= target_roll:
                        dmg = roll_dice(current_dice) if current_dice else 0
                        damage_by_target[id(target)] += dmg
                        hits_by_target[id(target)] += 1
                    else:
                        dmg = (roll_dice(current_dice) // 2) if current_dice else 0
                        damage_by_target[id(target)] += dmg
                        hits_by_target[id(target)] += 1
                        
                elif spell_type == "auto":
                    dmg = roll_dice(current_dice) if current_dice else 0
                    damage_by_target[id(target)] += dmg
                    hits_by_target[id(target)] += 1
                    
                    threshold = ability_data.get('hp_threshold')
                    if threshold and target.get('current_hp', target.get('hp', 999)) > threshold:
                        damage_by_target[id(target)] = 0
                        hits_by_target[id(target)] = 0
                        msg_parts.append(f"Target HP above threshold!")
                
                elif spell_type == "heal":
                    heal_amt = roll_dice(current_dice) if current_dice else 0
                    total_healing += heal_amt
                    hits_by_target[id(target)] += 1
                
                elif spell_type == "buff":
                    hits_by_target[id(target)] += 1

        # Consolidate results
        total_hits = sum(hits_by_target.values())
        total_damage = sum(damage_by_target.values())

        if is_aoe:
            msg_parts.append(f"AOE hit {len(active_targets)} targets!")
        elif iterations > 1:
            msg_parts.append(f"Landed {total_hits}/{iterations} hits!")
        elif total_hits > 0 and spell_type in ("attack", "save", "auto"):
            msg_parts.append(f"Dealt {total_damage} damage!")
        elif total_hits == 0 and spell_type in ("attack", "save"):
            msg_parts.append("It missed!")

        # Apply Effects (only if at least one hit landed)
        if total_hits > 0:
            # Handle standard effect
            effect_name = ability_data.get('effect')
            if effect_name:
                power = ability_data.get('power', 0)
                all_effects.append((effect_name, power if power else ability_data.get('duration', 1)))
                msg_parts.append(f"Effect: {effect_name.title()}")
            
            # Handle DOT/HOT
            if ability_data.get('dot'):
                dot_dice = ability_data.get('dot_dice', '1d6')
                # Store DOT info in effects to be handled by combat state
                all_effects.append(('dot', dot_dice))
                msg_parts.append("Lingering damage applied!")
            
            # Special effects like blind, death, etc.
            if ability_data.get('effect') == 'death':
                # Power Word Kill logic already handled by damage/auto check?
                # Actually PWK just kills if under threshold.
                pass

        return {
            'mana_cost': mana_cost,
            'damage': total_damage,
            'healing': total_healing,
            'damage_by_target': damage_by_target, # Map of id(target) -> damage
            'effects': all_effects,
            'hit': total_hits > 0,
            'msg': " ".join(msg_parts)
        }


    @staticmethod
    def resolve_item(item_data, user):
        """
        Resolves item usage.
        item_data: dict from consumables.json
        user: player/creature data
        """
        hp_gain = item_data.get('hp_gain', 0)
        bonus_gain = item_data.get('bonus_gain', 0)
        attack_gain = item_data.get('attack_gain', 0)
        extra_damage = item_data.get('extra_damage', 0)
        
        display_name = item_data.get('name', 'Item').replace('_', ' ').title()
        msg = f"Used {display_name}. {item_data.get('description', '')}"
        
        return {
            'hp_gain': hp_gain,
            'bonus_gain': bonus_gain,
            'attack_gain': attack_gain,
            'extra_damage': extra_damage,
            'msg': msg
        }

    @staticmethod
    def generate_loot(enemies):
        """
        Generates loot after defeating enemies.
        """
        total_gold = 0
        items = []
        messages = []
        
        for enemy in enemies:
            # Gold based on enemy HP/level
            gold = random.randint(5, 15) + (enemy.get('hp', 10) // 5)
            total_gold += gold
            
            # Chance for item
            if random.random() < 0.3:
                # Randomly pick a category and item (simplified)
                item_types = ['consumable', 'junk']
                t = random.choice(item_types)
                if t == 'consumable':
                    item_name = random.choice(['healing_potion', 'mana_potion'])
                else:
                    item_name = 'goblin_ear'
                items.append((t, item_name))
                messages.append(f"Found {item_name.replace('_', ' ').title()}!")

        messages.append(f"Gained {total_gold} gold!")
        
        return {
            'gold': total_gold,
            'items': items,
            'messages': messages
        }

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
