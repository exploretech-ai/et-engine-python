from flask import Flask, Response
import logging
import os

from base import CONNECTION_POOL, EFS_MOUNT_POINT
from base.key_authorizer import AuthMiddleware


app = Flask(__name__)
app.wsgi_app = AuthMiddleware(app.wsgi_app)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@app.route('/')
def hello():
    return "hello, world!"


@app.route('/vfs/<vfsID>/files/<path:filepath>', methods=['GET'])
def download_file(vfsID, filepath):

    logger.info(f"VFS: {vfsID}, File: {filepath}")

    full_file_path = os.path.join(EFS_MOUNT_POINT, vfsID, filepath)

    if "/../" in full_file_path:
        logger.info(f"** ALERT: POTENTIALLY MALICIOUS PATH **")
        return "Invalid path", 403
    
    if not os.path.exists(full_file_path):
        return f"File '{filepath}' does not exist", 404

    def stream_file(file_to_stream):
        with open(file_to_stream, "rb") as file_object:
            while True:
                chunk = file_object.read(8192)
                if not chunk:
                    break
                yield chunk
            
    return Response(stream_file(full_file_path))
    

if __name__ == '__main__':

    environment = os.environ.get("ENV", "prod")

    if environment == 'dev':
        app.run(host="0.0.0.0", port=80)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=80)
