from flask import Flask, send_file, send_from_directory, request
import logging
import os

app = Flask(__name__)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

EFS_MOUNT_POINT = '/mnt/'


@app.route('/vfs/<vfsID>/files/<path:filepath>', methods=['GET'])
def download_file(vfsID, filepath):
    
    logger.info(f"VFS: {vfsID}, File: {filepath}")

    return send_from_directory(EFS_MOUNT_POINT + vfsID, filepath, as_attachment=True)


if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=80)
