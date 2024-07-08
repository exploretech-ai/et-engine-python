import requests
import json
import os
from math import ceil
from tqdm import tqdm
import asyncio, aiohttp, aiofiles
from .config import API_ENDPOINT, MIN_CHUNK_SIZE_BYTES, MAX_CHUNK_SIZE_BYTES


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


    def upload(self, local_file, remote_file, chunk_size=MIN_CHUNK_SIZE_BYTES, timeout=7200):
        """Performs a multipart upload to s3
        
        Steps:
        1. Check the file's size and determine the number of parts needed
        2. Prepare the multipart upload with a POST request to Engine
        3. Upload the parts with asynchronous POST requests to s3 with the presigned urls
        4. Complete the multipart upload with another POST request to Engine with query string param ?complete=true
        
        """
        if chunk_size < MIN_CHUNK_SIZE_BYTES:
            raise ChunkTooSmallError("chunk size is too small")

        url = f"{self.url}/files/{remote_file}"

        # Step 1: determine parts
        file_size_bytes = os.stat(local_file).st_size
        num_parts = ceil(file_size_bytes / chunk_size)

        # Step 2: Get presigned urls
        upload_id, urls, chunk_size = request_multipart_upload(url, remote_file, num_parts, file_size_bytes, chunk_size)
        
        # Step 3: Upload part
        uploaded_parts = asyncio.run(upload_parts_in_parallel(local_file, urls, chunk_size, file_size_bytes, timeout=timeout))

        # Step 4: Complete upload
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
        
        if complete.status_code != 200:
            raise Exception(f"Error completing upload: {complete}, {complete.reason}, {complete.text}")

        # return Upload(complete.json())
    
    
    def download(self, remote_file, local_file):
        """Downloads a copy of a VFS file to the local machine

        Parameters
        ----------
        remote_file : string
            path to the remote copy of the file inside the VFS
        local_file : string
            path to the destination of the downloaded file
        
        """
        url = f"{self.url}/files/{remote_file}"

        response = requests.get(
            url, 
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
            self.url + "/mkdir/" + path, 
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        # >>>>> HERE CHANGE THIS SO "ALREADY EXISTS" DOESN'T THROW ERROR

        # =====
        response.raise_for_status()
        # <<<<<


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
        return upload_id, urls, chunk_size
    else:
        raise Exception(f"Error creating multipart upload: {response}, {response.reason}")
    
    


async def upload_part(local_file, part_number, chunk_size, presigned_url, session):
    """
    Uploads one part in a multipart upload
    """
    starting_byte = (part_number - 1) * chunk_size
    async with aiofiles.open(local_file, mode='rb') as file:
        await file.seek(starting_byte)
        chunk = await file.read(chunk_size)
        async with session.put(presigned_url, data=chunk) as status:
            if not status.ok:
                raise Exception(f"Error uploading part: {status}")
            
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
    
