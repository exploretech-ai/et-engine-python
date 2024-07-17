from flask import Flask
from base.api_key_methods import keys
from base.task_methods import tasks
from base.tool_methods import tools
from base.vfs_methods import vfs

def create_app():
    app = Flask(__name__)
    app.register_blueprint(keys)
    app.register_blueprint(tasks)
    app.register_blueprint(tools)
    app.register_blueprint(vfs)
    return app