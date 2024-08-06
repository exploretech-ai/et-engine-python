
API_ENDPOINT = "https://api-dev.exploretech.ai"
MIN_CHUNK_SIZE_BYTES = 8 * 1024 * 1024
MAX_CHUNK_SIZE_BYTES = 64 * 1024 * 1024

import requests
import json
import os
from math import ceil
import asyncio, aiohttp, aiofiles
from tqdm import tqdm
import time


class PayloadTooLargeError(Exception):
    pass


class ChunkTooSmallError(Exception):
    pass


class MultipartUploadPresignedUrls:
    def __init__(self, upload_id, urls, chunk_size):
        self.upload_id = upload_id
        self.urls = urls
        self.chunk_zie = chunk_size


class MultipartUpload:

    def __init__(self, local_file, endpoint_url, chunk_size=MIN_CHUNK_SIZE_BYTES, timeout=7200, method="POST"):
        self.local_file = local_file
        self.url = endpoint_url
        self.method = method

        self.file_size_bytes = os.stat(local_file).st_size
        self.num_parts = ceil(self.file_size_bytes / chunk_size)
        self.chunk_size = chunk_size

        self.timeout = timeout

        self.presigned_urls = None
        self.uploaded_parts = None

        
    def request_upload(self):
        response = requests.request(
            self.method,
            self.url, 
            data=json.dumps({
                "num_parts": self.num_parts
            }),
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        if response.status_code == 504:
            self.chunk_size = self.chunk_size * 2
            self.num_parts = ceil(self.file_size_bytes / self.chunk_size)

            if self.chunk_size > MAX_CHUNK_SIZE_BYTES:
                raise Exception("Chunk Size Too Large")
            print(f"Increasing chunk size to {self.chunk_size / 1024 / 1024} MB")
            return self.request_upload()
        
        if response.ok:
            response = response.json()
            upload_id = response["UploadId"]
            urls = response["urls"]

            self.presigned_urls = MultipartUploadPresignedUrls(upload_id, urls, self.chunk_size)
            return self.presigned_urls
        else:
            raise Exception(f"Error creating multipart upload: {response}, {response.text}")
        

    def upload(self):
        self.uploaded_parts = asyncio.run(self.upload_parts_in_parallel())


    def complete_upload(self):

        if self.uploaded_parts is None:
            raise Exception("Upload not yet complete")
        
        # Step 4: Complete upload
        complete = requests.request(
            self.method,
            self.url, 
            data=json.dumps({
                "complete": "true",
                "parts": self.uploaded_parts,
                "UploadId": self.presigned_urls.upload_id
            }),
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        
        if complete.status_code != 200:
            raise Exception(f"Error completing upload: {complete}, {complete.reason}, {complete.text}")

        
    async def upload_part(self, part_number, presigned_url, session):
        """
        Uploads one part in a multipart upload
        """
        starting_byte = (part_number - 1) * self.chunk_size
        async with aiofiles.open(self.local_file, mode='rb') as file:
            await file.seek(starting_byte)
            chunk = await file.read(self.chunk_size)
            async with session.put(presigned_url, data=chunk) as status:
                if not status.ok:
                    raise Exception(f"Error uploading part: {status.reason}, {status}")
                
                return {"ETag": status.headers["ETag"], "PartNumber": part_number}
            
        
    async def upload_parts_in_parallel(self):
        """
        Sends upload HTTP requests asynchronously to speed up file transfer
        """

        if self.presigned_urls is None:
            raise Exception("Upload not yet requested")

        client_timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            upload_part_tasks = set()
            for part_number, presigned_url in self.presigned_urls.urls: 
                task = asyncio.create_task(
                    self.upload_part(part_number, presigned_url, session)
                )
                upload_part_tasks.add(task)

            parts = []
            for task in tqdm(asyncio.as_completed(upload_part_tasks), desc=f"[{self.file_size_bytes / 1024 / 1024 // 1} MB] '{self.local_file}'", total=len(upload_part_tasks)):
                completed_part = await task
                parts.append(completed_part)

            return parts
        

class DirectMultipartUpload:

    def __init__(self, local_file, url, chunk_size=MIN_CHUNK_SIZE_BYTES, timeout=7200):
        self.local_file = local_file
        self.url = url

        self.file_size_bytes = os.stat(local_file).st_size
        self.num_parts = ceil(self.file_size_bytes / chunk_size)
        self.chunk_size = chunk_size

        self.timeout = timeout

        self.upload_id = None


    def request_upload(self):
        response = requests.post(
            self.url, 
            data=json.dumps({
                'size': self.file_size_bytes
            }), 
            headers={
                'Authorization': os.environ['ET_ENGINE_API_KEY']
            }
        )

        if response.ok:
            upload_details = response.json()
            self.upload_id = upload_details['upload_id']

    
    def upload(self):
        return asyncio.run(self.upload_parts_in_parallel())
    

    def complete_upload(self):
        if self.upload_id is None:
            raise Exception("Upload not yet initialized")
        
        response = requests.post(
            self.url,
            data=json.dumps({
                'upload_id': self.upload_id,
                'complete': True
            }),
            headers={
                'Authorization': os.environ['ET_ENGINE_API_KEY']
            }
        )
        response.raise_for_status()

    
    async def upload_part(self, starting_byte, session):
        """
        Uploads one part in a multipart upload
        """

        if self.upload_id is None:
            raise Exception("Upload not yet initialized")

        async with aiofiles.open(self.local_file, mode='rb') as file:

            await file.seek(starting_byte)
            chunk = await file.read(self.chunk_size)
            chunk_length = len(chunk)

            content_range = f"[{self.upload_id}]:{starting_byte}-{starting_byte+chunk_length}"

            headers = {
                'Authorization': os.environ['ET_ENGINE_API_KEY'],
                'Content-Range': content_range
            }

            n_tries = 0
            while n_tries < 5:
                try:
                    async with session.put(self.url, data=chunk, headers=headers) as response:
                        if not response.ok:
                            raise Exception(f"Error uploading part: {response.text}")
                        return response.status
                except:
                    n_tries += 1
            raise Exception("Max retries exceeded")
                            
        
    async def upload_parts_in_parallel(self):
        """
        Sends upload HTTP requests asynchronously to speed up file transfer
        """

        connector = aiohttp.TCPConnector(limit=5)
        client_timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=client_timeout, connector=connector) as session:
            upload_part_tasks = set()
            for starting_byte in range(0, self.file_size_bytes, self.chunk_size):
                task = asyncio.create_task(
                    self.upload_part(starting_byte, session)
                )
                upload_part_tasks.add(task)

            parts = []
            for task in tqdm(asyncio.as_completed(upload_part_tasks), desc=f"[{self.file_size_bytes / 1024 / 1024 // 1} MB] {self.local_file}", total=len(upload_part_tasks)):
                part_status = await task
                parts.append(part_status)

            return parts
        
    
class DirectMultipartDownload:

    def __init__(self, local_file, url, chunk_size=MIN_CHUNK_SIZE_BYTES, timeout=7200):
        self.local_file = local_file
        self.url = url

        self.file_size_bytes = None
        self.num_parts = None
        self.download_id = None
        self.chunk_size = chunk_size

        self.timeout = timeout

        

    
    def request_download(self):

        response = requests.get(
            self.url,
            params={
                "init": True
            },
            headers={
                'Authorization': os.environ['ET_ENGINE_API_KEY']
            }
        )
        if not response.ok:
            raise Exception(response.text)
    
        download_info = response.json()
        self.file_size_bytes = download_info['size']
        self.download_id = download_info['download_id']
        self.num_parts = ceil(self.file_size_bytes / self.chunk_size)

        self.initialize_file()


    def initialize_file(self):

        if self.file_size_bytes is None or self.download_id is None or self.num_parts is None:
            raise Exception("Download not yet initialized")
        
        destination = f"{self.local_file}.{self.download_id}"
        with open(destination, "wb") as f:
            f.seek(self.file_size_bytes - 1)
            f.write(b'\0')


    def download(self):
        return asyncio.run(self.download_parts_in_parallel())


    def complete_download(self):
        destination = f"{self.local_file}.{self.download_id}"
        os.rename(destination, self.local_file)


    async def download_part(self, starting_byte, session):
        """
        Uploads one part in a multipart upload
        """

        destination = f"{self.local_file}.{self.download_id}"
        async with aiofiles.open(destination, mode='r+b') as f:

            await f.seek(starting_byte, 0)
            content_range = f"{starting_byte}-{starting_byte+self.chunk_size}"

            headers = {
                'Authorization': os.environ['ET_ENGINE_API_KEY'],
                'Content-Range': content_range
            }

            n_tries = 0
            while n_tries < 1:
                try:
                    async with session.get(self.url, headers=headers) as response:
                        if not response.ok:
                            raise Exception(f"Error uploading part: {response.text}")
                        
                        await f.write(await response.content.read())
                        return response.status
                except:
                    n_tries += 1
            raise Exception("Max retries exceeded")
                            
        
    async def download_parts_in_parallel(self):
        """
        Sends upload HTTP requests asynchronously to speed up file transfer
        """

        connector = aiohttp.TCPConnector(limit=5)
        client_timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=client_timeout, connector=connector) as session:
            download_part_tasks = set()
            for starting_byte in range(0, self.file_size_bytes, self.chunk_size):
                task = asyncio.create_task(
                    self.download_part(starting_byte, session)
                )
                download_part_tasks.add(task)

            parts = []
            for task in tqdm(asyncio.as_completed(download_part_tasks), desc=f"[{self.file_size_bytes / 1024 / 1024 // 1} MB] {self.local_file}", total=len(download_part_tasks)):
                part_status = await task
                parts.append(part_status)

            return parts

