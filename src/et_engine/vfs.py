import requests
import json
import os
from .config import API_ENDPOINT

def create(name):	
    """Creates a new Tool	
        
    Parameters	
    ----------	
    name : string	
        Name of the tool	
    description : string	
        Plain text description of the tool	
    Returns	
    -------	
    Tool	
        A Tool object connected to the newly-created tool	
    Raises	
    ------	
    Warnings	
    --------	
    The API works, but the method does not yet return a connected "Tool" object	
    """	

    # API Request	
    status = requests.post(	
        API_ENDPOINT + "vfs",
        data=json.dumps({	
            "name": name
        }), 	
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}	
    )

    if status.ok:
        return status
    else:
        print(status)
        raise Exception('Create failed')


def connect(vfs_name):

    status = requests.get(
            API_ENDPOINT + "vfs", 
            params={'name':vfs_name},
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
    if status.ok:

        vfs_id = status.json()[0][1]
        return VirtualFileSystem(vfs_id)
    
    else:
        print(status)
        print(status.reason)
        raise NameError(f'Filesystem "{vfs_name}" does not exist')


def delete(name):	
    """deletes the specified VFS	
        
    Parameters	
    ----------	
    name : string	
        Name of the VFS to delete	
    """	
    status = requests.delete(	
        API_ENDPOINT + "vfs", 
        params={'name':name},	
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}	
    )	

    if status.ok:
        return status
    else:
        raise Exception('Delete failed')
        





class VirtualFileSystem:
    """Object for interacting with the ET Engine VFS API
    
    Attributes
    ----------
    session : Session
        authenticated session
    url : string
        VFS API endpoint
    """

    def __init__(self, vfs_id):
        """Creates a new object connected to the VFS
        
        Parameters
        ----------
        vfs_id : string
            id associated with the VFS of interest
        """
        self.id = vfs_id
        self.url = API_ENDPOINT + f"vfs/{vfs_id}"

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
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        response.raise_for_status()
        presigned_post = json.loads(response.text)
        # print(presigned_post)
        
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
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        presigned_url = json.loads(response.text)
        
        with requests.get(presigned_url, stream=True) as r:
            # r.raise_for_status()
            with open(local_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=None):
                    f.write(chunk)

    def mkdir(self, path):
        response = requests.post(
            self.url + "/mkdir", 
            data=json.dumps({"path": path}),
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        # >>>>> HERE CHANGE THIS SO "ALREADY EXISTS" DOESN'T THROW ERROR

        # =====
        response.raise_for_status()
        # <<<<<

    def list(self, path=None):

        params = {}
        if path is not None:
            params['path'] = path

        status = requests.get(	
            self.url + "/list", 
            params=params,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}	
        )	

        if status.ok:
            return status.json()
        else:
            print(status)
            raise Exception('List failed')

