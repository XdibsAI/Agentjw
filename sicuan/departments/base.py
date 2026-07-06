"""
Department Base - Base class untuk semua departemen
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class Department(ABC):
    """Base class untuk semua departemen"""

    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    @abstractmethod
    def get_status(self) -> Dict:
        """Dapatkan status departemen"""
        pass

    @abstractmethod
    def get_summary(self) -> str:
        """Dapatkan ringkasan departemen"""
        pass

    @abstractmethod
    def execute(self, action: str, params: Dict) -> Dict:
        """Eksekusi action di departemen"""
        pass

    def update_config(self, config: Dict):
        """Update konfigurasi departemen"""
        self.config.update(config)
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert ke dictionary"""
        return {
            "name": self.name,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class DepartmentManager:
    """Manager untuk semua departemen"""

    def __init__(self):
        self.departments = {}

    def register(self, department: Department):
        """Register departemen"""
        self.departments[department.name] = department
        print(f"[DEPT] Registered: {department.name}")

    def get(self, name: str) -> Optional[Department]:
        """Dapatkan departemen by name"""
        return self.departments.get(name)

    def list(self) -> list:
        """Daftar semua departemen"""
        return list(self.departments.keys())

    def get_all_status(self) -> Dict:
        """Dapatkan status semua departemen"""
        return {
            name: dept.get_status()
            for name, dept in self.departments.items()
        }

    def execute(self, dept_name: str, action: str, params: Dict) -> Dict:
        """Eksekusi action di departemen tertentu"""
        dept = self.get(dept_name)
        if not dept:
            return {"error": f"Department '{dept_name}' not found"}
        return dept.execute(action, params)
