from flask import Flask, Response, request
import os
import json
import random
import asyncio, aiofiles

app = Flask(__name__)

@app.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['GET'])
async def download_file(vfs_id, filepath):

    initialize = request.args.get('init', default=False)
    if initialize:
        file_size_bytes = os.stat(filepath).st_size
        sample_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        download_id = ''.join(random.choices(sample_str, k = 20))  
        payload = json.dumps({
            "size": file_size_bytes,
            "download_id": download_id
        })
        return Response(payload, status=200)

    try:
        if 'Content-Range' not in request.headers:
            return Response("Missing Content-Range header", status=400)
        
        content_range = [int(b) for b in request.headers['Content-Range'].strip().split("-")]
        chunk_size = content_range[1] - content_range[0]

        async with aiofiles.open(filepath, mode='rb') as file:
            await file.seek(content_range[0])
            chunk = await file.read(chunk_size)
            return Response(chunk, status=200)
        
    except Exception as e:
        print(e)
        return Response("Unknown error", status=500)


if __name__ == '__main__':

    environment = os.environ.get("ENV", "prod")

    if environment == 'dev':
        app.run(host="0.0.0.0", port=80)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=80)
