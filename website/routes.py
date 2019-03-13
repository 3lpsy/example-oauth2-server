from flask import Blueprint, request, session, current_app, url_for
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.flask.oauth2 import current_token
from authlib.specs.rfc6749 import OAuth2Error
from .models import db, User, OAuth2Client
from .oauth2 import authorization, require_oauth
from authlib.jose import JWK
from authlib.jose import JWK_ALGORITHMS

bp = Blueprint(__name__, 'home')


def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None


@bp.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        return redirect('/')
    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []
    return render_template('home.html', user=user, clients=clients)


@bp.route('/logout')
def logout():
    print("Logging out")

    del session['id']
    return redirect('/')


@bp.route('/create_client', methods=('GET', 'POST'))
def create_client():
    user = current_user()
    if not user:
        return redirect('/')
    if request.method == 'GET':
        return render_template('create_client.html')
    client = OAuth2Client(**request.form.to_dict(flat=True))
    client.user_id = user.id
    client.client_id = gen_salt(24)
    if client.token_endpoint_auth_method == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)
    db.session.add(client)
    db.session.commit()
    return redirect('/')



@bp.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    print("Current user", user)
    if request.method == 'GET':
        try:
            print("Validating consent request for end user:", user)
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            print("Error when valdiating consent request for end user:", error)
            print('Error class:', error.__class__.__name__)
            print('Error description:', error.description)
            print('Error uri:', error.uri)
            print('Error:', error.error)
            return error.error
        return render_template('authorize.html', user=user, grant=grant)
    print("Receieved post request to authorize:")
    if not user and 'username' in request.form:
        username = request.form.get('username')
        print("Username found in form:", username)
        user = User.query.filter_by(username=username).first()
    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    print("Creating authorization request for grant:", grant_user)

    grant = authorization.create_authorization_response(grant_user=grant_user)
    print('Grant created', grant)
    print('Grant class: ', grant.__class__.__name__)
    return grant

@bp.route('/oauth/token', methods=['POST'])
def issue_token():
    print("Issuing token response")
    return authorization.create_token_response()


@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')


@bp.route('/oauth/jwks.json', methods=['GET'])
def jwks_json():
    jwk = JWK(algorithms=JWK_ALGORITHMS)
    public_key_path = current_app.config.get('OAUTH2_JWT_PUBLIC_KEY_PATH')
    with open(public_key_path, 'r') as f:
        public_key = f.read()
    return jsonify({'keys' [jwk.dumps(public_key, kty='RSA')]})


@bp.route('/api/me')
@require_oauth('profile')
def api_me():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)

@bp.route('/.well_known/openid-configuration')
def openid_configuration():
    return jsonify({
        'authorization_endpoint': url_for('website.routes.authorize', _external=True, _scheme='https'),
        'jwks_uri': url_for('website.routes.jwks_json', _external=True, _scheme='https'),
        'issuer': current_app.config.get('OAUTH2_JWT_ISS')
    })
