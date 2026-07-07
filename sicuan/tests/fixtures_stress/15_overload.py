
from typing import overload

class Calculator:
    @overload
    def add(self, a: int, b: int) -> int:
        pass
