from website.app import create_app


app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'OAUTH2_JWT_ENABLED': True,
    'OAUTH2_JWT_ALG': 'RS256',
    'OAUTH2_JWT_KEY_PATH': Path('./jwt.pem').resolve(),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite',
})


@app.cli.command()
def initdb():
    from website.models import db
    db.create_all()
