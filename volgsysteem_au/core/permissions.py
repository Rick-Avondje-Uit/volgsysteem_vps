from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

def is_begeleider_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if (
            request.user.is_staff
            or request.user.groups.filter(name="Begeleider").exists()
        ):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper

