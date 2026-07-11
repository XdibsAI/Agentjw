"""
Context Memory - Simple context memory for SiCuan
"""

class ContextMemory:
    def __init__(self):
        self.memory = {}

    def get(self, key, default=None):
        return self.memory.get(key, default)

    def set(self, key, value):
        self.memory[key] = value

    def clear(self):
        self.memory = {}

    def get_all(self):
        return self.memory


def get_context_memory():
    return ContextMemory()
