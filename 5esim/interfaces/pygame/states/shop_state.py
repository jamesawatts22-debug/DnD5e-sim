from game.states.base_state import BaseState
from game.ui.menu import Menu
from game.ui.backgrounds import BackgroundManager
from players.player import load_weapons, load_armor, apply_weapon_to_player, apply_armor_to_player
from players.shop import load_consumables

class ShopState(BaseState):
    def __init__(self, game, font):
        super().__init__(game, font)
        self.background = BackgroundManager.get_shop_bg()

        self.inventory = game.player.get("inventory_ref", {})
        if not self.inventory:
             self.inventory = game.player.get("inventory", {})

        self.mode = "MAIN"
        self.item_map = {}

        self.main_menu = Menu(["Buy", "Sell", "Back"], font, width=200, header="The Dragon's Hoard")
        self.active_menu = self.main_menu

    def refresh_buy_menu(self):
        options = ["Weapons", "Armor", "Consumables", "Back"]
        self.active_menu = Menu(options, self.font, width=200, header="What are you looking for?")

    def open_buy_category(self, category):
        if category == "weapons":
            data = load_weapons().get("weapon_list", {})
        elif category == "armor":
            data = load_armor()
        elif category == "consumables":
            data = load_consumables()
        else:
            return

        available = {k: v for k, v in data.items() if v.get('cost', 0) > 0}
        names = sorted(available.keys())
        
        options = []
        self.item_map = {}
        for k in names:
            item = available[k]
            display_name = item.get('name', k.replace('_', ' ')).title()
            full_display = f"{display_name} ({item['cost']}g)"
            options.append(full_display)
            self.item_map[full_display] = k
            
        options.append("Back")
        self.active_menu = Menu(options, self.font, width=250, header=f"Available {category.title()}")

    def refresh_sell_list(self):
        # Sell junk logic
        junk_items = self.inventory.get('junk', [])
        if not junk_items:
            options = ["Back"]
            header = "You have no junk to sell."
        else:
            options = [f"Sell All Junk ({len(junk_items)}g)", "Back"]
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
                from game.states.hub import HubState
                self.game.change_state(HubState(self.game, self.font))

        elif self.mode == "BUY_CAT":
            if option == "Back":
                self.mode = "MAIN"
                self.active_menu = self.main_menu
            else:
                self.mode = "BUY_ITEMS"
                self.buy_category = option.lower()
                self.open_buy_category(self.buy_category)

        elif self.mode == "BUY_ITEMS":
            if option == "Back":
                self.mode = "BUY_CAT"
                self.refresh_buy_menu()
            else:
                self.handle_buy(option)

        elif self.mode == "SELL":
            if option == "Back":
                self.mode = "MAIN"
                self.active_menu = self.main_menu
            elif option.startswith("Sell All"):
                from players.shop import sell_junk
                sell_junk(self.inventory)
                self.refresh_sell_list()

    def handle_buy(self, display_name):
        item_key = self.item_map.get(display_name)
        if not item_key: return

        if self.buy_category == "weapons":
            data = load_weapons().get("weapon_list", {})
        elif self.buy_category == "armor":
            data = load_armor()
        else:
            data = load_consumables()

        item = data[item_key]
        cost = item['cost']
        
        # Check gold
        if self.game.god_mode or self.inventory.get('gold', 0) >= cost:
            if not self.game.god_mode:
                self.inventory['gold'] -= cost
            
            from players.player_inventory import add_item
            # Mapping Buy Categories to inventory keys (weapons -> weapon)
            inv_key = self.buy_category[:-1] if self.buy_category.endswith('s') else self.buy_category
            add_item(self.inventory, item_key, inv_key)
            
            print(f"Bought {item_key}")
            # Refresh to show you still have gold or if items are unique
            self.open_buy_category(self.buy_category)
        else:
            print("Not enough gold!")

    def draw(self, screen):
        super().draw(screen)

        from game.ui.panel import draw_text_outlined
        from constants import SCREEN_WIDTH, COLOR_GOLD
        
        title_text = "The Dragon's Hoard"
        tw, th = self.font.size(title_text)
        draw_text_outlined(screen, title_text, self.font, (255,255,255), (SCREEN_WIDTH // 2) - (tw // 2), 40)
        
        # Show Gold
        gold_text = f"Gold: {self.inventory.get('gold', 0)}"
        gw, gh = self.font.size(gold_text)
        draw_text_outlined(screen, gold_text, self.font, COLOR_GOLD, (SCREEN_WIDTH // 2) - (gw // 2), 80)
        
        # Menu is drawn by base_state if we set self.menu, but HubState does it manually.
        # We'll do it manually to match HubState style.
        if self.active_menu:
            width, height = screen.get_size()
            self.active_menu.draw(screen, width // 2, height // 2)