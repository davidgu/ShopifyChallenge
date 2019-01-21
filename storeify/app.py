from flask import Flask
from flask_graphql import GraphQLView

from storeify.db import get_db_session
from storeify.schema import schema


def create_app(debug=True, database=None):
    app = Flask(__name__)
    app.debug = True

    app.add_url_rule(
        '/graphql',
        view_func=GraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True
        )
    )

    app.teardown_appcontext

    def shutdown_session(exception=None):
        get_db_session.remove()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run
