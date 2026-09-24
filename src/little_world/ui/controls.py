"""Input state only; no native viewer shortcuts or solver types."""
class DriveInput:
    def __init__(self):
        self.held = set()

    def press(self, key):
        self.held.add(key)

    def release(self, key):
        self.held.discard(key)

    def clear(self):
        self.held.clear()

    def targets(self):
        forward = int('W' in self.held) - int('S' in self.held)
        turn = int('A' in self.held) - int('D' in self.held)
        return (5. * forward - 2.5 * turn, 5. * forward + 2.5 * turn)
