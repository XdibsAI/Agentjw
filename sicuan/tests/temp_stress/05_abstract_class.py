
from abc import ABC, abstractmethod

class Base(ABC):
    @abstractmethod
    def doit(self):
        pass
