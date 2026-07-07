"""Test fixture - wrong class name"""
class Strategy2:
    def __init__(self):
        self.running = True
    
    def run(self):
        return True
