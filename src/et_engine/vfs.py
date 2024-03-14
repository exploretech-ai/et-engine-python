import requests
import json


class VirtualFileSystem:

    def __init__(self, vfs_id, session):
        self.session = session
        self.url = session.API_ENDPOINT + f"vfs/{vfs_id}"

    def file_exists(self):
        pass

    def upload(self, local_file, remote_file):
        presigned_post = requests.post(
            self.url, 
            data=json.dumps({"key": remote_file}),
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        return presigned_post.text
        upload_url = json.loads(presigned_post.text)
        
        with open(local_file, 'rb') as f:
            files = {'file': (local_file, f)}
            upload_response = requests.post(
                upload_url['url'], 
                data=upload_url['fields'], 
                files=files
            )

        return upload_response.text
    
    def download(self, remote_file, local_file):
        pass
