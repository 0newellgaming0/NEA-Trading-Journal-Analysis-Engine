from .xp_events import XPEvent
from .xp_rules import calculate_xp
from .xp_storage import XPStorage
from .xp_notifier import XPNotifier
from .xp_tracker import XPTracker


class XPSystem:

    def __init__(self):
        self.storage = XPStorage()
        self.notifier = XPNotifier()
        self.tracker = XPTracker(self.storage, self.notifier)

        self.milestones = {
            5: "Consistency Beginner",
            10: "System Operator",
            25: "Market Analyst",
            50: "Institutional Mindset",
            100: "Elite Operator",
        }

    def handle_event(self, event_type: str, metadata=None):
        event = XPEvent(event_type, metadata or {})

        xp = calculate_xp(event)

        level, remaining_xp = self.tracker.add_xp(xp)

        self.notifier.xp_gain(xp, event_type)

        self.check_milestones(level)

        return {
            "xp_gained": xp,
            "level": level,
            "remaining_xp": remaining_xp
        }

    def check_milestones(self, level):
        if level in self.milestones:
            self.notifier.milestone(self.milestones[level])