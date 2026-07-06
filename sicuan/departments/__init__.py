"""
Departments Module
"""

from sicuan.departments.base import Department, DepartmentManager
from sicuan.departments.finance import FinanceDepartment

# Create manager
manager = DepartmentManager()

# Register departments
manager.register(FinanceDepartment())

print(f"[DEPT] Registered departments: {manager.list()}")
