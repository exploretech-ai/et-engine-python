import requests
from typing import Self

import et_engine_core as etc
from . import clients


class Filesystem(etc.Filesystem):
    """An Interface and Client for interacting with an ET Engine Filesystem.
    """

    def __init__(self, base_url: str, *args, **kwargs) -> None:
        """Create an interactive ET Engine Filesystem object.

        Args:
            base_url (str): Base endpoint for requests.
        """

        super().__init__(*args, **kwargs)
        self.client = clients.APIClient(f"{base_url}/filesystems/{self.filesystem_id}")


    def upload(self, local_file: str, remote_file: str, chunk_size: int = clients.MIN_CHUNK_SIZE_BYTES) -> None:
        """Uploads a local file to the specified path on The Engine.

        Args:
            local_file (str): A valid path to file on the local filesystem.
            remote_file (str): A valid path to the destination of the remote file, starting from the filesystem root.
            chunk_size (int, optional): Size of each chunk, in bytes. Defaults to clients.MIN_CHUNK_SIZE_BYTES.
        """
        
        url = f"{self.client.url}/files/{remote_file}"
        file_contents = clients.MultipartUpload(local_file, url, chunk_size=chunk_size)
        file_contents.request_upload()
        file_contents.upload()
        file_contents.complete_upload()

    
    def download(self, remote_file: str, local_file: str, chunk_size: int = clients.MIN_CHUNK_SIZE_BYTES) -> None:
        """Downloads a copy of a filesystem file to the local machine

        Args:
            remote_file (str): Path to the remote copy of the file inside the filesystem
            local_file (str): Path to the destination of the downloaded file
            chunk_size (int, optional): Size of each chunk, in bytes. Defaults to clients.MIN_CHUNK_SIZE_BYTES.
        """

        url = f"{self.client.url}/files/{remote_file}"
        file_contents = clients.MultipartDownload(local_file, url, chunk_size=chunk_size)
        file_contents.request_download()
        file_contents.download()
        file_contents.complete_download()


    def mkdir(self, path: str, ignore_exists: bool = False) -> None:
        """Make a new directory in the remote filesystem.

        Args:
            path (str): Path to the new directory.
            ignore_exists (bool, optional): Whether to ignore errors caused by the directory already existing. Defaults to False.
        """

        try:
            self.client.post(f"/mkdir/{path}")
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 409 and ignore_exists:
                return


    def delete(self, path: str) -> None:
        """Delete a file on the remote filesystem.

        Args:
            path (str): Path to the file to be deleted.
        """
        self.client.delete(f"/files/{path}")


    def ls(self, path: str = '') -> dict[str, list]:
        """List contents of a directory within a filesystem.

        Args:
            path (str, optional): Path to the directory to perform the ls command. Defaults to ''.

        Returns:
            dict[str, list]: A dictionary with keys ['directories', 'files'], each of which maps to a list of directories and files within the requested directory, respsectively.
        """
        
        return self.client.get(f"/list/{path}")
    

    @staticmethod
    def from_json(base_url: str, filesystem_json: dict) -> Self:
        """Convert a JSON object to an interactive Filesystem.

        Args:
            base_url (str): Base endpoint for requests.
            filesystem_json (dict): JSON description of the Filesystem.

        Returns:
            Self: A Filesystem object.
        """
        base_filesystem = etc.Filesystem.from_json(filesystem_json)
        new_filesystem = Filesystem(
            base_url,
            filesystem_id=base_filesystem.filesystem_id, 
            filesystem_name=base_filesystem.filesystem_name
        )
        return new_filesystem
    

class FilesystemsClient(clients.APIClient):
    """Client for interacting with ET Engine Filesystems.
    """

    def __init__(self, base_url: str = clients.DEFAULT_BASE_URL) -> None:
        """Create a new client for interacting with ET Engine Filesystems.

        Args:
            base_url (str, optional): Base endpoint for requests. Defaults to clients.DEFAULT_BASE_URL.
        """
        
        super().__init__(f"{base_url}/filesystems")
        self.base_url = base_url


    def create_filesystem(self, filesystem_name: str) -> Filesystem:
        """Creates a new ET Engine Filesystem resource.

        Args:
            filesystem_name (str): Unique name of the filesystem to create.

        Returns:
            Filesystem: A new interactive Filesystem object.
        """

        data = {
            "filesystem_name": filesystem_name
        }
        filesystem_json = self.post(data=data)
        return Filesystem.from_json(self.base_url, filesystem_json)


    def list_filesystems(self) -> list[Filesystem]:
        """List all the available filesystems.

        Returns:
            list[Filesystem]: A list of Filesystem clients.
        """

        filesystem_list = self.get()
        return [Filesystem.from_json(self.base_url, fs) for fs in filesystem_list]
    

    def connect(self, filesystem_name: str) -> Filesystem:
        """Connect the client to a specific Filesystem resource.

        Args:
            filesystem_name (str): Name of the filesystem to connect to.

        Raises:
            Exception: A filesystem with the specified name does not exist.

        Returns:
            Filesystem: A new interactive Filesystem object for the specified filesystem.
        """

        filesystem_list = self.list_filesystems()
        for fs in filesystem_list:
            if fs.filesystem_name == filesystem_name:
                return fs
        raise Exception("Filesystem does not exist")