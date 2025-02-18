# Auto-generated script
class ItemScript:
    def __init__(self, item):
        self.item = item

    def on_hit(self, target):
        """Custom hit behavior"""
        import random
        if random.random() < 0.1:  # 10% chance
            if hasattr(target, 'apply_effect'):
                target.apply_effect('bleeding', duration=5000)
                print(f"{self.item.name} caused bleeding effect!")
