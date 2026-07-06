"""
Departments Module
"""

from sicuan.departments.base import Department, DepartmentManager
from sicuan.departments.finance import FinanceDepartment
from sicuan.departments.strategy import StrategyDepartment

# Create manager
manager = DepartmentManager()

# Register departments
manager.register(FinanceDepartment())
manager.register(StrategyDepartment())

print(f"[DEPT] Registered departments: {manager.list()}")
