from website.app import create_app
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

app = create_app({
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'OAUTH2_REFRESH_TOKEN_GENERATOR': os.getenv('OAUTH2_REFRESH_TOKEN_GENERATOR') == "1",
    'OAUTH2_JWT_ENABLED': os.getenv('OAUTH2_JWT_ENABLED') == "1",
    'OAUTH2_JWT_ALG': os.getenv('OAUTH2_JWT_ALG'),
    'OAUTH2_JWT_KEY_PATH': str(Path(os.getenv('OAUTH2_JWT_KEY_PATH')).resolve()),
    'OAUTH2_JWT_PUBLIC_KEY_PATH': str(Path(os.getenv('OAUTH2_JWT_PUBLIC_KEY_PATH')).resolve()),
    'SQLALCHEMY_TRACK_MODIFICATIONS': os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS') == "1",
    'OAUTH2_JWT_ISS': os.getenv('OAUTH2_JWT_ISS'),
    'OAUTH2_JWT_EXP': os.getenv('OAUTH2_JWT_EXP'),
    'SQLALCHEMY_DATABASE_URI': os.getenv('SQLALCHEMY_DATABASE_URI')
})


def initialize_database(app):
    from website.models import db
    with app.app_context():
        db.create_all()

@app.cli.command()
def initdb():
    initialize_database(app)

def list_urls(app):
    from werkzeug.exceptions import MethodNotAllowed, NotFound
    rows = []
    column_length = 0
    column_headers = ('Rule', 'Endpoint', 'Arguments')
    url = None
    order = 'rule'
    with app.app_context():
        if url:
            try:
                rule, arguments = (
                    app.url_map
                               .bind('localhost')
                               .match(url, return_rule=True))
                rows.append((rule.rule, rule.endpoint, arguments))
                column_length = 3
            except (NotFound, MethodNotAllowed) as e:
                rows.append(('<{}>'.format(e), None, None))
                column_length = 1
        else:
            rules = sorted(
                app.url_map.iter_rules(),
                key=lambda rule: getattr(rule, order))
            for rule in rules:
                rows.append((rule.rule, rule.endpoint, None))
            column_length = 2

        str_template = ''
        table_width = 0

        if column_length >= 1:
            max_rule_length = max(len(r[0]) for r in rows)
            max_rule_length = max_rule_length if max_rule_length > 4 else 4
            str_template += '{:' + str(max_rule_length) + '}'
            table_width += max_rule_length

        if column_length >= 2:
            max_endpoint_length = max(len(str(r[1])) for r in rows)
            # max_endpoint_length = max(rows, key=len)
            max_endpoint_length = (
                max_endpoint_length if max_endpoint_length > 8 else 8)
            str_template += '  {:' + str(max_endpoint_length) + '}'
            table_width += 2 + max_endpoint_length

        if column_length >= 3:
            max_arguments_length = max(len(str(r[2])) for r in rows)
            max_arguments_length = (
                max_arguments_length if max_arguments_length > 9 else 9)
            str_template += '  {:' + str(max_arguments_length) + '}'
            table_width += 2 + max_arguments_length
        print(str_template.format(*column_headers[:column_length]))
        print('-' * table_width)

        for row in rows:
            print(str_template.format(*row[:column_length]))
    return 0

@app.cli.command()
def urls():
    list_urls(app)
