"""
Departments Module
"""

from sicuan.departments.base import Department, DepartmentManager
from sicuan.departments.finance import FinanceDepartment
from sicuan.departments.strategy import StrategyDepartment
from sicuan.departments.curriculum import CurriculumDepartment

# Create manager
manager = DepartmentManager()

# Register departments
manager.register(FinanceDepartment())
manager.register(StrategyDepartment())
manager.register(CurriculumDepartment())

print(f"[DEPT] Registered departments: {manager.list()}")
