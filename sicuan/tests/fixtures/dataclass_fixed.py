from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    def move(self):
        return self.x + self.y
