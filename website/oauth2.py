from authlib.flask.oauth2 import AuthorizationServer, ResourceProtector
from authlib.flask.oauth2.sqla import (
    create_query_client_func,
    create_save_token_func,
    create_revocation_endpoint,
    create_bearer_token_validator,

)
from authlib.specs.rfc6749 import grants
from authlib.specs.oidc import grants as oidc_grants

from werkzeug.security import gen_salt
from .models import db, User
from .models import OAuth2Client, OAuth2AuthorizationCode, OAuth2Token


class OpenIDCodeGrant(oidc_grants.OpenIDCodeGrant):
    def create_authorization_code(self, client, grant_user, request):
        print("OpenIDCodeGrant: Creating authorization code")
        code = generate_token(48)
        nonce = request.data.get('nonce')
        item = OAuth2AuthorizationCode(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            nonce=nonce,
            user_id=grant_user.get_user_id(),
        )
        print("OpenIDCodeGrant: Saving OAuth2AuthorizationCode")
        db.session.add(item)
        db.session.commit()
        return code

    def parse_authorization_code(self, code, client):
        print("OpenIDCodeGrant: Parsing Authorization code", code)
        print("OpenIDCodeGrant: Parsing Authorization client", client)
        item = OAuth2AuthorizationCode.query.filter_by(
            code=code, client_id=client.client_id).first()
        if item and not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        print("OpenIDCodeGrant: Deleting Authorization code", authorization_code)
        db.session.delete(authorization_code)
        db.session.commit()

    def authenticate_user(self, authorization_code):
        print("OpenIDCodeGrant: Authenticating user", authorization_code)
        return User.query.get(authorization_code.user_id)


class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    def authenticate_user(self, username, password):
        print("PasswordGrant: Authenticating user with password", username)
        user = User.query.filter_by(username=username).first()
        if user.check_password(password):
            return user


class RefreshTokenGrant(grants.RefreshTokenGrant):
    def authenticate_refresh_token(self, refresh_token):
        print("RefreshTokenGrant: Authenticating refresh token", refresh_token)
        item = OAuth2Token.query.filter_by(refresh_token=refresh_token).first()
        if item and not item.is_refresh_token_expired():
            return item

    def authenticate_user(self, credential):
        print("RefreshTokenGrant: Authenticating user", credential)
        return User.query.get(credential.user_id)


query_client = create_query_client_func(db.session, OAuth2Client)
save_token = create_save_token_func(db.session, OAuth2Token)
authorization = AuthorizationServer(
    query_client=query_client,
    save_token=save_token,
)
require_oauth = ResourceProtector()


def config_oauth(app):
    authorization.init_app(app)

    # support all grants
    authorization.register_grant(grants.ImplicitGrant)
    authorization.register_grant(grants.ClientCredentialsGrant)
    authorization.register_grant(PasswordGrant)
    authorization.register_grant(RefreshTokenGrant)

    authorization.register_grant(OpenIDCodeGrant)
    authorization.register_grant(oidc_grants.OpenIDImplicitGrant)

    # support revocation
    revocation_cls = create_revocation_endpoint(db.session, OAuth2Token)
    authorization.register_endpoint(revocation_cls)

    # protect resource
    bearer_cls = create_bearer_token_validator(db.session, OAuth2Token)
    require_oauth.register_token_validator(bearer_cls())
