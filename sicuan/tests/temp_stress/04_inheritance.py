
class Base:
    def method(self):
        return "base"

class Child(Base):
    def method(self):
        return super().method() + " child"
