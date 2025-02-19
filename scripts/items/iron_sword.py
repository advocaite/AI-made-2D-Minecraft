class ItemScript:
    def __init__(self, item):
        self.item = item
        print(f"[IRON SWORD] Script initialized for {item.name}")

    def on_hit(self, target):
        """Apply bleeding effect with 10% chance"""
        import random
        
        if hasattr(target, 'apply_effect'):
            if random.random() < 0.1:  # 10% chance
                print(f"[IRON SWORD] Applying bleeding effect!")
                target.apply_effect('bleeding', duration=5000)
                return True
        return False

    def get_tooltip_info(self):
        """Return tooltip information about this script's effects"""
        return [
            "Effects:",
            "• 10% chance to cause bleeding",
            "• Bleeding deals 1 damage/second",
            "• Effect lasts 5 seconds"
        ]
