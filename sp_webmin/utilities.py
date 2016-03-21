from functools import wraps

from flask import render_template
from flask_login import current_user


permissions = set()


def permission_required(permission):
    permissions.add(permission)

    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if current_user.has_permission(permission):
                return func(*args, **kwargs)
            else:
                return render_template("error.html", data="You are not authorized to view this page")
        return decorated_view
    return decorator
