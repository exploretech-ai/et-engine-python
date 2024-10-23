from .clients import DEFAULT_BASE_URL
from .tools import ToolsClient
from .filesystems import FilesystemsClient
from .batches import BatchesClient


class Engine:
    """Main client for interacting with the ET Engine.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        """Create a new Engine client.

        Args:
            base_url (str, optional): Base endpoint for requests. Defaults to DEFAULT_BASE_URL.
        """
        self.filesystems = FilesystemsClient(base_url)
        self.tools = ToolsClient(base_url)
        self.batches = BatchesClient(base_url)
