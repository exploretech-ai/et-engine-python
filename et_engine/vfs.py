import requests
import json
import os
from math import ceil
from tqdm import tqdm
import asyncio, aiohttp, aiofiles
from .config import API_ENDPOINT, MIN_CHUNK_SIZE_BYTES, DirectMultipartUpload, DirectMultipartDownload


class PayloadTooLargeError(Exception):
    pass


class ChunkTooSmallError(Exception):
    pass


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
        API_ENDPOINT + "/vfs",
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


def list_all():
    status = requests.get(
        API_ENDPOINT + "/vfs", 
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
    )
    if status.ok:
        vfs_list = status.json()
        return vfs_list
    else:
        raise Exception("unknown error occurred while listing VFS")


def connect(vfs_name):

    vfs_list = list_all()

    for row in vfs_list:
        if row[0] == vfs_name:
            return VirtualFileSystem(row[1])
    
    raise NameError(f'Filesystem "{vfs_name}" does not exist')


def delete(name):	
    """deletes the specified VFS	
        
    Parameters	
    ----------	
    name : string	
        Name of the VFS to delete	
    """	
    status = requests.delete(	
        API_ENDPOINT + "/vfs", 
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
        self.url = API_ENDPOINT + f"/vfs/{vfs_id}"


    def file_exists(self):
        pass


    def upload(self, local_file, remote_file, chunk_size=MIN_CHUNK_SIZE_BYTES):
        """Performs a multipart upload to s3
        
        Steps:
        1. Check the file's size and determine the number of parts needed
        2. Prepare the multipart upload with a POST request to Engine
        3. Upload the parts with asynchronous POST requests to s3 with the presigned urls
        4. Complete the multipart upload with another POST request to Engine with query string param ?complete=true
        
        """
        url = f"{self.url}/files/{remote_file}"

        file_contents = DirectMultipartUpload(local_file, url, chunk_size=chunk_size)
        file_contents.request_upload()
        file_contents.upload()
        file_contents.complete_upload()

    
    def download(self, remote_file, local_file, chunk_size=MIN_CHUNK_SIZE_BYTES):
        """Downloads a copy of a VFS file to the local machine

        Parameters
        ----------
        remote_file : string
            path to the remote copy of the file inside the VFS
        local_file : string
            path to the destination of the downloaded file
        
        """
        url = f"{self.url}/files/{remote_file}"

        file_contents = DirectMultipartDownload(local_file, url, chunk_size=chunk_size)
        file_contents.request_download()
        file_contents.download()
        file_contents.complete_download()


    def mkdir(self, path, ignore_exists=False):
        response = requests.post(
            self.url + "/mkdir/" + path, 
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        if ignore_exists and response.status_code == 409:
            return
        
        response.raise_for_status()


    def delete(self, path):
        response = requests.delete(
            self.url + "/files/" + path, 
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        response.raise_for_status()


    def list(self, path=None):

        params = {}
        url = self.url + "/list/"
        if path is not None:
            url += path

        status = requests.get(	
            url, 
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}	
        )	

        if status.ok:
            return status.json()
        else:
            print(status)
            raise Exception('List failed')

