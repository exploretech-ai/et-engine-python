import requests
import json


class VirtualFileSystem:
    """Object for interacting with the ET Engine VFS API
    
    Attributes
    ----------
    session : Session
        authenticated session
    url : string
        VFS API endpoint
    """

    def __init__(self, vfs_id, client):
        """Creates a new object connected to the VFS
        
        Parameters
        ----------
        vfs_id : string
            id associated with the VFS of interest
        client : Client
            base authenticated client containing the active session
        """
        self.session = client.session
        self.url = client.API_ENDPOINT + f"vfs/{vfs_id}"

    def file_exists(self):
        pass

    def upload(self, local_file, remote_file):
        """Uploads a file to the VFS

        Parameters
        ----------
        local_file : string
            path to the local copy of the file to upload
        remote_file : string
            path to the remote copy of the uploaded file inside the VFS

        
        """
        response = requests.post(
            self.url, 
            data=json.dumps({"key": remote_file}),
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        response.raise_for_status()
        presigned_post = json.loads(response.text)
        print(presigned_post)
        
        with open(local_file, 'rb') as f:
            files = {'file': (local_file, f)}
            upload_response = requests.post(
                presigned_post['url'], 
                data=presigned_post['fields'], 
                files=files
            )

        return upload_response
    
    def download(self, remote_file, local_file):
        """Downloads a copy of a VFS file to the local machine

        Parameters
        ----------
        remote_file : string
            path to the remote copy of the file inside the VFS
        local_file : string
            path to the destination of the downloaded file
        
        """
        response = requests.get(
            self.url, 
            params={"key": remote_file},
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        presigned_url = json.loads(response.text)
        
        with requests.get(presigned_url, stream=True) as r:
            # r.raise_for_status()
            with open(local_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=None):
                    f.write(chunk)

