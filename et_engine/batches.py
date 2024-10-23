import time
from tqdm import tqdm
from typing import Self

import et_engine_core as etc
from . import clients


class Batch(etc.Batch):
    """An Interface & Client for interacting with an ET Engine Batch.
    """

    def __init__(self, base_url: str, *args, **kwargs) -> None:
        """Create an interactive ET Engine Batch object.

        Args:
            base_url (str): Base endpoint for requests.
        """
    
        super().__init__(*args, **kwargs)
        self.client = clients.APIClient(f"{base_url}/batches/{self.batch_id}")


    def delete(self) -> None:
        """Delete this batch. 
        * NOTE: This will not cancel any jobs, which will still run and incur costs once deleted.
        """
        self.client.delete()
        

    def status(self, max_retries: int = 5) -> etc.BatchStatus:
        """Fetches a summary of the status of all jobs in the Batch.

        Args:
            max_retries (int, optional): Number of requests to try before raising an exception. Defaults to 5.

        Raises:
            Exception: Max retries exceeded.

        Returns:
            etc.BatchStatus: An et_engine_core.BatchStatus object summarizing the status of all jobs in the Batch.
        """

        num_tries = 0
        while num_tries < max_retries:

            try:
                batch_status_json = self.client.get()
                return etc.BatchStatus.from_json(batch_status_json)
            
            except:
                num_tries += 1

        raise Exception("max retries exceeded")
        

    def wait(self, interval: int = 15, thresh: int = None) -> None:
        """Wait for the Batch to finish processing.

        Args:
            interval (int, optional): Number of seconds between status refreshes, in seconds. Defaults to 15.
            thresh (int, optional): Threshold number of jobs to finish waiting, if None then it waits until all jobs finish. Defaults to None.
        """

        status = self.status()

        if thresh is None:
            thresh = self.n_jobs

        with tqdm(total=self.n_jobs) as pbar:

            status = self.status()
            completed = status.succeeded + status.failed
                
            while completed < thresh:

                time.sleep(interval)
                status = self.status()
                completed = status.succeeded + status.failed
                pbar.update(completed - pbar.n)


    @staticmethod
    def from_json(base_url: str, batch_json: dict) -> Self:
        """Convert a JSON object to an interactive Batch.

        Args:
            base_url (str): Base endpoint for requests.
            batch_json (dict): JSON description of the Batch.

        Returns:
            Self: A Batch object.
        """
        return Batch(base_url, **batch_json)


class BatchesClient(clients.APIClient):
    """Client for interacting with ET Engine Batches.
    """
    
    def __init__(self, base_url: str = clients.DEFAULT_BASE_URL) -> None:
        """Create a new client for interacting with ET Engine Batches.

        Args:
            base_url (str, optional): Base endpoint for requests. Defaults to clients.DEFAULT_BASE_URL.
        """

        super().__init__(f"{base_url}/batches")
        self.base_url = base_url

    
    def list_batches(self) -> list[Batch]:
        """Lists all the available batches.

        Returns:
            list[Batch]: A list of Batch clients to each available resource.
        """

        batches_list = self.get()
        return [Batch.from_json(self.base_url, b) for b in batches_list]


    def clear_batches(self) -> None:
        """Deletes all batches.
        """
        self.delete()

