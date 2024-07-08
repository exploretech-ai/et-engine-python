from flask import Flask, send_file, send_from_directory, request, Response
import logging
import os

app = Flask(__name__)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

EFS_MOUNT_POINT = '/mnt/'


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
    
    # return send_from_directory(EFS_MOUNT_POINT + vfsID, filepath, as_attachment=True)


if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=80)
