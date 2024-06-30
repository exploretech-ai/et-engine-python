import requests
import json
import os
from .config import API_ENDPOINT, MIN_CHUNK_SIZE_BYTES, MAX_CHUNK_SIZE_BYTES
from math import ceil
from pathlib import Path
from tqdm import tqdm
import asyncio, aiohttp, aiofiles


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


def list_all():
    status = requests.get(
        API_ENDPOINT + "vfs", 
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


class ChunkTooSmallError(Exception):
    pass


async def upload_part(local_file, part_number, chunk_size, presigned_url, session):
    """
    Uploads one part in a multipart upload
    """
    starting_byte = part_number * chunk_size
    async with aiofiles.open(local_file, mode='rb') as file:
        await file.seek(starting_byte)
        chunk = await file.read(chunk_size)
        async with session.put(presigned_url, data=chunk) as status:
            if not status.ok:
                raise Exception(f"Error uploading part: {status.status_code} {status.reason} {status.text}")
            
            return {"ETag": status.headers["ETag"], "PartNumber": part_number}
        
    
async def upload_parts_in_parallel(local_file, urls, chunk_size, file_size, timeout=3600):
    """
    Sends upload HTTP requests asynchronously to speed up file transfer
    """

    client_timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        upload_part_tasks = set()
        for part_number, presigned_url in urls: 
            task = asyncio.create_task(
                upload_part(local_file, part_number, chunk_size, presigned_url, session)
            )
            upload_part_tasks.add(task)

        parts = []
        for task in tqdm(asyncio.as_completed(upload_part_tasks), desc=f"[{file_size / 1024 / 1024 // 1} MB] '{local_file}'", total=len(upload_part_tasks)):
            completed_part = await task
            parts.append(completed_part)

        return parts
    

def upload_parts_sequential(local_file, urls, chunk_size):
    parts = []
    print('in sequence')
    for part_number, presigned_url in tqdm(urls, total=len(urls)):
        starting_byte = part_number * chunk_size
        with open(local_file, 'rb') as file:
            file.seek(starting_byte)
            chunk = file.read(chunk_size)
            status = requests.put(presigned_url, data=chunk)
            if not status.ok:
                raise Exception(f"Error uploading part: {status.status_code} {status.reason} {status.text}")

        parts.append({"ETag": status.headers["ETag"], "PartNumber": part_number})

    return parts


def request_multipart_upload(url, remote_file, num_parts, file_size_bytes, chunk_size):
    response = requests.post(
        url, 
        data=json.dumps({
            "key": remote_file,
            "num_parts": num_parts
        }),
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
    )

    if response.status_code == 504:
        chunk_size = chunk_size * 2
        num_parts = ceil(file_size_bytes / chunk_size)

        if chunk_size > MAX_CHUNK_SIZE_BYTES:
            raise Exception("Chunk Size Too Large")
        print(f"Increasing chunk size to {chunk_size / 1024 / 1024} MB")
        return request_multipart_upload(url, remote_file, num_parts, file_size_bytes, chunk_size)
    
    if response.ok:
        response = response.json()
        upload_id = response["UploadId"]
        urls = response["urls"]
    else:
        raise Exception(f"Error creating multipart upload: {response}, {response.reason}")
    
    return upload_id, urls, chunk_size

class PayloadTooLargeError(Exception):
    pass


def multipart_upload(local_file, remote_file, chunk_size=MIN_CHUNK_SIZE_BYTES, timeout=7200):
    """Performs a multipart upload to s3
    
    Steps:
    1. Check the file's size and determine the number of parts needed
    2. Prepare the multipart upload with a POST request to Engine
    3. Upload the parts with asynchronous POST requests to s3 with the presigned urls
    4. Complete the multipart upload with another POST request to Engine with query string param ?complete=true
    
    """
    if chunk_size < MIN_CHUNK_SIZE_BYTES:
        raise ChunkTooSmallError("chunk size is too small")
    url = API_ENDPOINT + "tmp"


    # Step 1: determine parts
    file_size_bytes = os.stat(local_file).st_size
    num_parts = ceil(file_size_bytes / chunk_size)

    # Step 2: Get presigned urls
    upload_id, urls, chunk_size = request_multipart_upload(url, remote_file, num_parts, file_size_bytes, chunk_size)
    
    # Step 3: Upload part
    uploaded_parts = asyncio.run(upload_parts_in_parallel(local_file, urls, chunk_size, file_size_bytes, timeout=timeout))
    # upladed_parts = upload_parts_sequential(local_file, urls, chunk_size)

    # Step 4: Complete upload
    # uploaded_parts = sorted(uploaded_parts, key=lambda x: x['PartNumber'])
    complete = requests.post(
        url, 
        data=json.dumps({
            "key": remote_file,
            "complete": "true",
            "parts": uploaded_parts,
            "UploadId": upload_id
        }),
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
    )
    
    if not complete.ok:
        raise Exception(f"Error completing upload: {complete}, {complete.reason}, {complete.text}")


def multipart_download(remote_file, local_file):
    url = API_ENDPOINT + "tmp"
    response = requests.get(
        url, 
        params={"key": remote_file},
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
    )
    print(response)
    presigned_url = response.json()
    
    
    with requests.get(presigned_url, stream=True) as r:
        # r.raise_for_status()
        with open(local_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=None):
                f.write(chunk)

