"""
Departments Module
"""

from sicuan.departments.base import Department, DepartmentManager
from sicuan.departments.finance import FinanceDepartment
from sicuan.departments.strategy import StrategyDepartment
from sicuan.departments.sop import SOPDepartment
from sicuan.departments.branding import BrandingDepartment
from sicuan.departments.hr import HRDepartment
from sicuan.departments.curriculum import CurriculumDepartment

# Create manager
manager = DepartmentManager()

# Register departments
manager.register(FinanceDepartment())
manager.register(StrategyDepartment())
manager.register(CurriculumDepartment())
manager.register(HRDepartment())
manager.register(BrandingDepartment())
manager.register(SOPDepartment())

print(f"[DEPT] Registered departments: {manager.list()}")
