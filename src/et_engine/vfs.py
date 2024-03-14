import requests
import json


class VirtualFileSystem:

    def __init__(self, vfs_id, session):
        self.session = session
        self.url = session.API_ENDPOINT + f"vfs/{vfs_id}"

    def file_exists(self):
        pass

    def upload(self, local_file, remote_file):
        response = requests.post(
            self.url, 
            data=json.dumps({"key": remote_file}),
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        presigned_post = json.loads(response.text)
        
        with open(local_file, 'rb') as f:
            files = {'file': (local_file, f)}
            upload_response = requests.post(
                presigned_post['url'], 
                data=presigned_post['fields'], 
                files=files
            )

        return upload_response
    
    def download(self, remote_file, local_file):
        response = requests.get(
            self.url, 
            params={"key": remote_file},
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        presigned_url = json.loads(response.text)
        
        with requests.get(presigned_url, stream=True) as r:
            r.raise_for_status()
            with open(local_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=None):
                    f.write(chunk)

