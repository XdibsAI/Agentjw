"""Test fixture - duplicate method"""
class Strategy:
    def __init__(self):
        self.running = True
    
    def run(self):
        return True
    
    def run(self):
        return False
