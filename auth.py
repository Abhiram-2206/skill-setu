"""
auth.py — Authentication Blueprint for Skill Setu
Supports: manual email/password  +  Google / LinkedIn / Facebook / Yahoo OAuth
"""

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from database import get_connection
import os

auth_bp = Blueprint('auth', __name__)
oauth    = OAuth()

# ── OAuth provider registration ────────────────────────────────────────────────

def init_oauth(app):
    oauth.init_app(app)

    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    oauth.register(
        name='linkedin',
        client_id=os.environ.get('LINKEDIN_CLIENT_ID'),
        client_secret=os.environ.get('LINKEDIN_CLIENT_SECRET'),
        access_token_url='https://www.linkedin.com/oauth/v2/accessToken',
        authorize_url='https://www.linkedin.com/oauth/v2/authorization',
        api_base_url='https://api.linkedin.com/v2/',
        client_kwargs={'scope': 'openid profile email'},
    )

    oauth.register(
        name='facebook',
        client_id=os.environ.get('FACEBOOK_CLIENT_ID'),
        client_secret=os.environ.get('FACEBOOK_CLIENT_SECRET'),
        access_token_url='https://graph.facebook.com/oauth/access_token',
        authorize_url='https://www.facebook.com/dialog/oauth',
        api_base_url='https://graph.facebook.com/',
        client_kwargs={'scope': 'email,public_profile'},
    )

    oauth.register(
        name='yahoo',
        client_id=os.environ.get('YAHOO_CLIENT_ID'),
        client_secret=os.environ.get('YAHOO_CLIENT_SECRET'),
        access_token_url='https://api.login.yahoo.com/oauth2/get_token',
        authorize_url='https://api.login.yahoo.com/oauth2/request_auth',
        api_base_url='https://api.login.yahoo.com/',
        client_kwargs={'scope': 'openid email profile'},
        jwks_uri='https://login.yahoo.com/.well-known/openid-configuration',
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_account_by_email(email):
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    row = conn.execute('SELECT * FROM accounts WHERE email = ?', (email,)).fetchone()
    conn.close()
    return row


def get_account_by_id(account_id):
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    row = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,)).fetchone()
    conn.close()
    return row


def get_or_create_oauth_account(provider, provider_id, name, email, avatar_url=None):
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    row = conn.execute(
        'SELECT * FROM accounts WHERE provider = ? AND provider_id = ?',
        (provider, provider_id)
    ).fetchone()

    if not row:
        # If same email exists from another provider, link it
        existing = conn.execute('SELECT * FROM accounts WHERE email = ?', (email,)).fetchone()
        if existing:
            conn.execute(
                'UPDATE accounts SET provider=?, provider_id=?, avatar_url=? WHERE id=?',
                (provider, provider_id, avatar_url, existing['id'])
            )
            conn.commit()
            row = conn.execute('SELECT * FROM accounts WHERE id=?', (existing['id'],)).fetchone()
        else:
            conn.execute(
                'INSERT INTO accounts (name, email, provider, provider_id, avatar_url) VALUES (?,?,?,?,?)',
                (name, email, provider, provider_id, avatar_url)
            )
            conn.commit()
            row = conn.execute('SELECT * FROM accounts WHERE email=?', (email,)).fetchone()

    conn.close()
    return row


# ── Manual auth routes ─────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        error = None
        if not name or not email or not password:
            error = 'All fields are required.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif get_account_by_email(email):
            error = 'An account with that email already exists.'

        if error:
            return render_template('register.html', error=error, name=name, email=email)

        conn = get_connection()
        conn.execute(
            'INSERT INTO accounts (name, email, password_hash, provider) VALUES (?,?,?,?)',
            (name, email, generate_password_hash(password), 'local')
        )
        conn.commit()
        conn.close()

        account = get_account_by_email(email)
        user = _make_user(account)
        login_user(user, remember=True)
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        account = get_account_by_email(email)

        if not account or not account.get('password_hash') or \
           not check_password_hash(account['password_hash'], password):
            return render_template('login.html', error='Invalid email or password.', email=email)

        user = _make_user(account)
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# ── OAuth routes ───────────────────────────────────────────────────────────────

@auth_bp.route('/auth/<provider>')
def oauth_login(provider):
    if provider not in ('google', 'linkedin', 'facebook', 'yahoo'):
        return redirect(url_for('auth.login'))
    client   = oauth.create_client(provider)
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri)


@auth_bp.route('/auth/<provider>/callback')
def oauth_callback(provider):
    if provider not in ('google', 'linkedin', 'facebook', 'yahoo'):
        return redirect(url_for('auth.login'))

    client = oauth.create_client(provider)

    try:
        token = client.authorize_access_token()
    except Exception as e:
        return render_template('login.html', error=f'OAuth error: {e}')

    name, email, provider_id, avatar_url = None, None, None, None

    try:
        if provider == 'google':
            userinfo    = token.get('userinfo') or client.userinfo()
            name        = userinfo.get('name')
            email       = userinfo.get('email')
            provider_id = userinfo.get('sub')
            avatar_url  = userinfo.get('picture')

        elif provider == 'linkedin':
            me   = client.get('https://api.linkedin.com/v2/userinfo').json()
            name = (me.get('given_name', '') + ' ' + me.get('family_name', '')).strip()
            email       = me.get('email')
            provider_id = me.get('sub')
            avatar_url  = me.get('picture')

        elif provider == 'facebook':
            me   = client.get('me?fields=id,name,email,picture').json()
            name        = me.get('name')
            email       = me.get('email')
            provider_id = me.get('id')
            avatar_url  = me.get('picture', {}).get('data', {}).get('url')

        elif provider == 'yahoo':
            userinfo    = client.userinfo()
            name        = userinfo.get('name')
            email       = userinfo.get('email')
            provider_id = userinfo.get('sub')
            avatar_url  = userinfo.get('picture')

    except Exception as e:
        return render_template('login.html', error=f'Could not fetch user info: {e}')

    if not email:
        return render_template('login.html', error='Could not retrieve email from provider.')

    account = get_or_create_oauth_account(provider, str(provider_id), name or email, email, avatar_url)
    user    = _make_user(account)
    login_user(user, remember=True)
    return redirect(url_for('dashboard'))


# ── User loader helper ─────────────────────────────────────────────────────────

def _make_user(account):
    from app import AccountUser
    return AccountUser(
        id=account['id'],
        name=account['name'],
        email=account['email'],
        avatar_url=account.get('avatar_url')
    )
