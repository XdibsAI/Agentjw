"""Test fixture - missing method _check_cooldown"""
class Strategy:
    def __init__(self):
        self.running = True
    
    def run(self):
        if self._check_cooldown():
            return False
        return True
