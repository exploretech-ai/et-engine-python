from flask import Flask, Response, request
import os
import json

from base.authorizer import Authorization

from base.vfs_methods import vfs
from base.tool_methods import tools
from base.task_methods import tasks
from base.api_key_methods import keys


app = Flask(__name__)
app.wsgi_app = Authorization(app.wsgi_app)

app.register_blueprint(vfs)
app.register_blueprint(tools)
app.register_blueprint(tasks)
app.register_blueprint(keys)


@app.after_request
def add_cors_header(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    return response


@app.route("/")
def health_check():
    return Response(status=200)


if __name__ == '__main__':

    environment = os.environ.get("ENV", "prod")

    if environment == 'dev':
        app.run(host="0.0.0.0", port=80)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=80)
