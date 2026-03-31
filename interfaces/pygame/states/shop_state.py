from interfaces.pygame.states.base_state import BaseState
from interfaces.pygame.ui.menu import Menu
from interfaces.pygame.ui.backgrounds import BackgroundManager
from core.players.player import load_weapons, load_armor, load_trinkets, load_shields, apply_weapon_to_player, apply_armor_to_player
from core.players.shop import load_consumables

class ShopState(BaseState):
    def __init__(self, game, font):
        super().__init__(game, font)
        self.background = BackgroundManager.get_shop_bg()

        self.inventory = game.player.get("inventory_ref", {})
        if not self.inventory:
             self.inventory = game.player.get("inventory", {})

        self.mode = "MAIN"
        self.item_map = {}
        self.buy_category = None
        self.current_page = 0
        self.items_per_page = 10

        self.main_menu = Menu(["Buy", "Sell", "Back"], font, width=100, header="The Dragon's Hoard")
        self.active_menu = self.main_menu

    def refresh_buy_menu(self):
        options = ["Weapons", "Armor", "Shields", "Consumables", "Trinkets", "Back"]
        self.active_menu = Menu(options, self.font, width=100, header="What are you looking for?")

    def open_buy_category(self, category):
        if category == "weapons":
            data = load_weapons().get("weapon_list", {})
        elif category == "armor":
            data = load_armor()
        elif category == "shields":
            data = load_shields()
        elif category == "consumables":
            data = load_consumables()
        elif category == "trinkets":
            data = load_trinkets()
        else:
            return

        available = {k: v for k, v in data.items() if v.get('cost', 0) > 0}
        
        if category == "armor":
            from core.players.player import can_equip_armor
            available = {k: v for k, v in available.items() if can_equip_armor(self.game.player, k)}
            # none > light > medium > heavy > robe
            type_order = {'none': 0, 'light': 1, 'medium': 2, 'heavy': 3, 'robe': 4}
            all_keys = sorted(available.keys(), key=lambda k: (type_order.get(available[k].get('type', 'none'), 99), available[k].get('cost', 0)))
        else:
            all_keys = sorted(available.keys(), key=lambda k: available[k].get('cost', 0))
        
        total_pages = (len(all_keys) + self.items_per_page - 1) // self.items_per_page
        if self.current_page >= total_pages: self.current_page = 0
        if self.current_page < 0: self.current_page = total_pages - 1

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_keys = all_keys[start_idx:end_idx]

        options = []
        descriptions = {}
        self.item_map = {}
        for k in page_keys:
            item = available[k]
            display_name = item.get('name', k.replace('_', ' ')).title()
            full_display = f"{display_name} ({item['cost']}g)"
            options.append(full_display)
            self.item_map[full_display] = k
            
            # Format description
            if category == "weapons":
                desc = f"{item.get('description', '')} (D{item.get('die', 4)}, {item.get('on_hit_effect', 'none').title()})"
            elif category == "armor":
                desc = f"{item.get('description', '')} (AC: {item.get('ac', 10)}, {item.get('type', 'light').title()})"
            elif category == "shields":
                desc = f"{item.get('description', '')} (AC: +{item.get('ac', 0)})"
            elif category == "trinkets":
                desc = item.get('description', '')
            else:
                desc = item.get('description', '')
            descriptions[full_display] = desc

        # Add Pagination/Footer options
        if total_pages > 1:
            options.append("Next Page")
            options.append("Previous Page")
        
        options.append("Return")
        
        header = f"{category.title()} (Page {self.current_page + 1}/{total_pages})"
        self.active_menu = Menu(options, self.font, width=200, header=header, descriptions=descriptions)

    def refresh_sell_list(self):
        # Sell junk logic
        junk_category = self.inventory.get('junk', {})
        total_junk = sum(junk_category.values()) if isinstance(junk_category, dict) else len(junk_category)
        
        if total_junk == 0:
            options = ["Back"]
            header = "You have no junk to sell."
        else:
            options = [f"Sell All Junk ({total_junk}g)", "Back"]
            header = f"Sell your junk items for 1g each?"
            
        self.active_menu = Menu(options, self.font, width=250, header=header)

    def on_select(self, option):
        if self.mode == "MAIN":
            if option == "Buy":
                self.mode = "BUY_CAT"
                self.refresh_buy_menu()
            elif option == "Sell":
                self.mode = "SELL"
                self.refresh_sell_list()
            elif option == "Back":
                from interfaces.pygame.states.hub import HubState
                self.game.change_state(HubState(self.game, self.font))

        elif self.mode == "BUY_CAT":
            if option == "Back":
                self.mode = "MAIN"
                self.active_menu = self.main_menu
            else:
                self.mode = "BUY_ITEMS"
                self.buy_category = option.lower()
                self.current_page = 0
                self.open_buy_category(self.buy_category)

        elif self.mode == "BUY_ITEMS":
            if option == "Return":
                self.mode = "BUY_CAT"
                self.refresh_buy_menu()
            elif option == "Next Page":
                self.current_page += 1
                self.open_buy_category(self.buy_category)
            elif option == "Previous Page":
                self.current_page -= 1
                self.open_buy_category(self.buy_category)
            elif option == "Back": # Fallback for old menus
                self.mode = "BUY_CAT"
                self.refresh_buy_menu()
            else:
                self.handle_buy(option)

        elif self.mode == "SELL":
            if option == "Back":
                self.mode = "MAIN"
                self.active_menu = self.main_menu
            elif option.startswith("Sell All"):
                from core.players.shop import sell_junk
                sell_junk(self.inventory)
                self.refresh_sell_list()

    def handle_buy(self, display_name):
        item_key = self.item_map.get(display_name)
        if not item_key: return

        if self.buy_category == "weapons":
            data = load_weapons().get("weapon_list", {})
        elif self.buy_category == "armor":
            data = load_armor()
        elif self.buy_category == "shields":
            data = load_shields()
        elif self.buy_category == "trinkets":
            data = load_trinkets()
        else:
            data = load_consumables()

        item = data[item_key]
        cost = item['cost']
        
        # Check gold
        if self.game.god_mode or self.inventory.get('gold', 0) >= cost:
            if not self.game.god_mode:
                self.inventory['gold'] -= cost
            
            from core.players.player_inventory import add_item
            # Mapping Buy Categories to inventory keys
            inv_key = self.buy_category[:-1] if self.buy_category.endswith('s') else self.buy_category
            add_item(self.inventory, item_key, inv_key)
            
            # Refresh current page
            self.open_buy_category(self.buy_category)
        else:
            print("Not enough gold!")

    def draw(self, screen):
        # --- Draw background FIRST ---
        self.draw_background(screen)

        width, height = screen.get_size()
        from core.game_rules.constants import scale_x, scale_y, SCREEN_WIDTH, COLOR_GOLD
        from interfaces.pygame.ui.panel import draw_text_outlined
        
        # Show Gold at the top
        gold_text = f"Gold: {self.inventory.get('gold', 0)}"
        gw, gh = self.font.size(gold_text)
        draw_text_outlined(screen, gold_text, self.font, COLOR_GOLD, (SCREEN_WIDTH // 2) - (gw // 2), scale_y(40))

        # --- MENU (Left Aligned, Vertically Centered) ---
        if self.active_menu:
            menu_width = self.active_menu.get_width()
            menu_height = len(self.active_menu.options) * scale_y(30) + (scale_y(40) if self.active_menu.header else 0) + scale_y(20)
            
            # Left align with padding (50px), center vertically
            menu_x = scale_x(50) + menu_width // 2
            menu_y = (height // 2) - (menu_height // 2)
            
            self.active_menu.draw(screen, menu_x, menu_y)
