"""
Adapters - Data access layer abstraction
"""
from .project_adapter import ProjectAdapter, get_project_adapter

__all__ = ['ProjectAdapter', 'get_project_adapter']
