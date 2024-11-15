import os
import requests
import json
import math

import asyncio
import aiohttp
import aiofiles

from tqdm import tqdm


MIN_CHUNK_SIZE_BYTES = 8 * 1024 * 1024
MAX_CHUNK_SIZE_BYTES = 64 * 1024 * 1024
DEFAULT_BASE_URL = "https://api.exploretech.ai/v1"


class APIClient:
    """Base client for interacting with the ET Engine API
    """

    def __init__(self, url: str = DEFAULT_BASE_URL) -> None:
        """Creates a new base client.

        Args:
            url (str, optional): Base endpoint in URL format. Defaults to DEFAULT_BASE_URL.
        """
        self.url = url


    def request(self, method: str, path: str, headers: dict = {}, params: dict = {}, data: dict = {}) -> dict:
        """Base method for making a request to the base endpoint.

        Args:
            method (str): HTTP method to make request to. Supported options are ["GET", "POST", "DELETE"].
            path (str): Resource path appended to the base URL.
            headers (dict, optional): Key-value pairs of headers to send with the request. Defaults to {}.
            params (dict, optional): Key-value pairs of query string params to send with the request. Defaults to {}.
            data (dict, optional): Key-value paris of request body to data to send with the request. Formatted as a JSON-like dictionary. Defaults to {}.

        Returns:
            dict: The response data formatted as a JSON-like dictionary.
        """

        response = requests.request(
            method,
            f"{self.url}{path}",
            headers=headers,
            params=params,
            data=json.dumps(data)
        )
        response.raise_for_status()
        if response.text:
           return response.json()
    

    def authorized_request(self, method: str, path: str, headers: dict = {}, params: dict = {}, data: dict = {}) -> dict:
        """Similar to the `request` method, but adds an API key authorization header.

        Args:
            method (str): HTTP method to make request to. Supported options are ["GET", "POST", "DELETE"].
            path (str): Resource path appended to the base URL.
            headers (dict, optional): Key-value pairs of headers to send with the request. Defaults to {}.
            params (dict, optional): Key-value pairs of query string params to send with the request. Defaults to {}.
            data (dict, optional): Key-value paris of request body to data to send with the request. Formatted as a JSON-like dictionary. Defaults to {}.

        Returns:
            dict: The response data formatted as a JSON-like dictionary.
        """

        headers["Authorization"] = os.environ["ET_ENGINE_API_KEY"]
        return self.request(method, path, headers=headers, params=params, data=data)


    def get(self, path: str = "", params: dict = {}) -> dict:
        """Performs a GET request with authorization at the specified resource path.

        Args:
            path (str, optional): Resource path appended to the base URL. Defaults to "".
            params (dict, optional): Query string params to send with the request. Defaults to {}.

        Returns:
            dict: The response data formatted as a JSON-like dictionary.
        """

        return self.authorized_request("GET", path, params=params)
        

    def post(self, path: str = "", data: dict = {}) -> dict:
        """Performs a POST request with authorization at the specified resource path.

        Args:
            path (str, optional): Resource path appended to the base URL. Defaults to "".
            data (dict, optional): Request body data to send with the request, in a JSON-like dictionary. Defaults to {}.

        Returns:
            dict: The response data formatted as a JSON-like dictionary.
        """

        return self.authorized_request("POST", path, data=data)
        

    def delete(self, path: str = "") -> dict:
        """Performs a DELETE request with authorization at the specified resource path.

        Args:
            path (str, optional): Resource path appended to the base URL. Defaults to "".

        Returns:
            dict: The response data formatted as a JSON-like dictionary.
        """

        return self.authorized_request("DELETE", path)
        

class MultipartUpload:
    """Client for handling parallelized multipart uploads to ET Engine.

    NOTE: This needs to be combined with Multipart Download because of duplicate code.
    """

    def __init__(self, local_file: str, url: str, chunk_size: int = MIN_CHUNK_SIZE_BYTES, timeout: int = 7200) -> None:
        """Create a new Multipart Upload job.

        Args:
            local_file (str): Valid path the local file to upload.
            url (str): Full URL of the remote file destination.
            chunk_size (int, optional): Size of each chunk, in bytes. Defaults to MIN_CHUNK_SIZE_BYTES.
            timeout (int, optional): Client timeout, in seconds. Defaults to 7200.
        """

        self.local_file = local_file
        self.url = url

        self.file_size_bytes = os.stat(local_file).st_size
        self.num_parts = math.ceil(self.file_size_bytes / chunk_size)

        self.chunk_size = chunk_size
        self.timeout = timeout
        self.upload_id = None


    def request_upload(self) -> None:
        """Initialize the upload with a POST request.
        """

        response = requests.post(
            self.url, 
            data=json.dumps({
                'size': self.file_size_bytes
            }), 
            headers={
                'Authorization': os.environ['ET_ENGINE_API_KEY']
            }
        )

        response.raise_for_status()
        upload_details = response.json()
        self.upload_id = upload_details['uploadId']
        
    
    def upload(self) -> None:
        """Launch the parallelized upload.
        """

        asyncio.run(self.upload_parts_in_parallel())
    

    def complete_upload(self) -> None:
        """Confirm the upload is complete with a POST request.

        Raises:
            Exception: The upload has not been initialized yet.
        """

        if self.upload_id is None:
            raise Exception("Upload not yet initialized")
        
        response = requests.post(
            self.url,
            data=json.dumps({
                'uploadId': self.upload_id,
                'complete': True
            }),
            headers={
                'Authorization': os.environ['ET_ENGINE_API_KEY']
            }
        )

        response.raise_for_status()

    
    async def upload_part(self, starting_byte: int, session: aiohttp.ClientSession) -> int:
        """Uploads one part in a multipart upload.

        Args:
            starting_byte (int): Index of the first byte in the part.
            session (aiohttp.ClientSession): The base asynchronous client session.

        Raises:
            Exception: The upload has not yet been initialized.
            Exception: Something went wrong with the upload.
            Exception: Max retries exceeded.

        Returns:
            int: HTTP status code of the response.
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
                            
        
    async def upload_parts_in_parallel(self) -> list[int]:
        """Creates the parallelized upload tasks and defines how they run, but does not execute them.

        Returns:
            list[int]: A list of HTTP status codes.
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
        
    
class MultipartDownload:
    """Client for handling parallelized multipart downloads to ET Engine.

    NOTE: This needs to be combined with Multipart Upload because of duplicate code.
    """

    def __init__(self, local_file: str, url: str, chunk_size: int = MIN_CHUNK_SIZE_BYTES, timeout: int = 7200) -> None:
        """Create a new Multipart Download job.

        Args:
            local_file (str): Valid path the local file to upload.
            url (str): Full URL of the remote file source.
            chunk_size (int, optional): Size of each chunk, in bytes. Defaults to MIN_CHUNK_SIZE_BYTES.
            timeout (int, optional): Client timeout, in seconds. Defaults to 7200.
        """
        self.local_file = local_file
        self.url = url

        self.file_size_bytes = None
        self.num_parts = None
        self.download_id = None
        self.chunk_size = chunk_size

        self.timeout = timeout

        
    def request_download(self) -> None:
        """Initialize the download with a GET request.
        """

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
        self.num_parts = math.ceil(self.file_size_bytes / self.chunk_size)

        self.initialize_file()


    def initialize_file(self) -> None:
        """Creates a local file to be filled in parts during the download.

        Raises:
            Exception: The download has not been initialized.
        """

        if self.file_size_bytes is None or self.download_id is None or self.num_parts is None:
            raise Exception("Download not yet initialized")
        
        destination = f"{self.local_file}.{self.download_id}"
        with open(destination, "wb") as f:
            f.seek(self.file_size_bytes - 1)
            f.write(b'\0')


    def download(self) -> None:
        """Launch the paralellized download.
        """

        asyncio.run(self.download_parts_in_parallel())


    def complete_download(self) -> None:
        """Complete the download by renaming the temporary file
        """
        
        destination = f"{self.local_file}.{self.download_id}"
        os.rename(destination, self.local_file)


    async def download_part(self, starting_byte: int, session: aiohttp.ClientSession) -> int:
        """Downloads one part in the multipart download.

        Args:
            starting_byte (int): Index of the first byte in the part.
            session (aiohttp.ClientSession): The base asynchronous client session.

        Raises:
            Exception: Something went wrong with the upload.
            Exception: Max retries exceeded.

        Returns:
            int: HTTP status code of the response.
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
                            
        
    async def download_parts_in_parallel(self) -> list[int]:
        """Creates the parallelized download tasks and defines how they run, but does not execute them.

        Returns:
            list[int]: A list of HTTP status codes.
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