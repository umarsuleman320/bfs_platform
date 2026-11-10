from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(*roles):
    """
    Usage: @role_required('mentor', 'coordinator')
    """
    def check(user):
        # 1. If they aren't logged in at all, return False. 
        # (user_passes_test will redirect them to the login page).
        if not user.is_authenticated:
            return False
            
        # 2. If they are logged in AND have the right role, let them in.
        if user.role in roles:
            return True
            
        # 3. If they are logged in but have the WRONG role (e.g., Mentee trying to access Management),
        # throw a strict "Access Denied" error instead of redirecting to login.
        raise PermissionDenied
        
    return user_passes_test(check, login_url='accounts:login')