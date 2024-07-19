
API_ENDPOINT = "https://api-dev.exploretech.ai"
MIN_CHUNK_SIZE_BYTES = 8 * 1024 * 1024
MAX_CHUNK_SIZE_BYTES = 64 * 1024 * 1024

import requests
import json
import os
from math import ceil
import asyncio, aiohttp, aiofiles
from tqdm import tqdm


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
                    raise Exception(f"Error uploading part: {status}")
                
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
        
