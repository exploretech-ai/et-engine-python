from flask import Flask, send_file, request
import os

app = Flask(__name__)

EFS_MOUNT_POINT = '/mnt/efs'

# @app.route('/download', methods=['GET'])
# def download_file():
#     filename = request.args.get('filename')
#     if filename:
#         file_path = os.path.join(EFS_MOUNT_POINT, filename)
#         if os.path.exists(file_path):
#             return send_file(file_path, as_attachment=True)
#         else:
#             return "File not found", 404
#     else:
#         return "Filename not provided", 400

@app.route("/")
def hello_world():
    print("Hello logs!")
    return "Hello, World!"

if __name__ == '__main__':
    print("initiating server")
    app.run(host='0.0.0.0', port=80)
