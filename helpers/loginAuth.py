from functools import wraps

from flask import redirect, session, url_for, flash


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            flash('You need to be logged in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function
