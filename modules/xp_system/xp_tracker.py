from .xp_levels import xp_required_for_level


class XPTracker:

    def __init__(self, storage, notifier):
        self.storage = storage
        self.notifier = notifier

    def add_xp(self, amount):
        current_xp = self.storage.get_xp()
        current_level = self.storage.get_level()

        new_xp = current_xp + amount

        # level-up loop
        while new_xp >= xp_required_for_level(current_level):
            new_xp -= xp_required_for_level(current_level)
            current_level += 1
            self.notifier.level_up(current_level)

        self.storage.set_xp(new_xp)
        self.storage.set_level(current_level)

        return current_level, new_xp