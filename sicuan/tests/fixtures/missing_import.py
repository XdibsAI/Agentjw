"""Test fixture - missing import"""
from typing import List

class Strategy:
    def __init__(self):
        self.data: List[str] = []
    
    def get_data(self) -> List[str]:
        return self.data
