"""Decorators for permission checking"""

from functools import wraps
from sicuan.core.permission_engine import get_permission_engine

def require_permission(action: str, resource: str = None):
    """Decorator to require permission for method"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get user from self or kwargs
            user = getattr(self, 'user', kwargs.get('user', 'default'))
            
            # Check permission
            engine = get_permission_engine()
            if not engine.check_permission(user, action, resource):
                raise PermissionError(
                    f"User {user} not authorized for {action}"
                )
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

def admin_only(func):
    """Decorator for admin-only methods"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        user = getattr(self, 'user', kwargs.get('user', 'default'))
        engine = get_permission_engine()
        
        if not engine.check_permission(user, "admin:*"):
            raise PermissionError(f"User {user} not authorized (admin only)")
        
        return func(self, *args, **kwargs)
    return wrapper
