class XPNotifier:

    @staticmethod
    def xp_gain(amount, reason):
        print(f"+{amount} XP → {reason}")

    @staticmethod
    def level_up(new_level):
        print(f"\n🎉 LEVEL UP! You are now Level {new_level}\n")

    @staticmethod
    def milestone(message):
        print(f"🏆 Milestone unlocked: {message}")