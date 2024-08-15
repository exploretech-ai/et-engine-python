import requests
from tqdm import tqdm
import os
import time
from .config import API_ENDPOINT


def list_batches():
    """
    Lists all the available batches for the user

    Parameters
    ----------

    Returns
    -------
    A list of Batch objects
    
    """
     
    response = requests.get(
        API_ENDPOINT + "/batches",
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
    )

    if response.ok:
        body = response.json()
        batches = [Batch(item["batch_id"]) for item in body]
        return batches
    else:
        raise


def clear_batches():
    """Deletes all the available batches for the user.
    
    * NOTE: This will not cancel any jobs, which will still run and incur costs once cleared.
    """

    response = requests.delete(
        API_ENDPOINT + "/batches",
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
    )
    if not response.ok:
        raise


class Batch:
    """Class for interacting with a Batch
    
    Attributes
    ----------
    id : 
        unique ID of the batch
    url : string
        API endpoint for this batch
    """
    def __init__(self, batch_id):
        """
        
        Parameters
        ----------
        batch_id : string
            The batch ID to connect to

        """
        self.id = batch_id
        self.url = API_ENDPOINT + "/batches/" + batch_id
        
    def list_jobs(self):
        """
        List the jobs in this batch

        Returns
        -------
        a lit of Job objects
        """
        
        response = requests.get(
            self.url + "/jobs",
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        if response.ok:
            jobs = response.json()
            return [Job(self.id, j["job_id"]) for j in jobs]
        else:
            raise Exception("error listing jobs: " + response.text)
        
    def delete(self):
        """Delete this batch. 
        * NOTE: This will not cancel any jobs, which will still run and incur costs once deleted.
        """

        response = requests.delete(
            self.url,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        if not response.ok:
            raise Exception("error deleting batch: " + response.text)
        
    def status(self):
        """
        Returns the basic information of this batch and summarizes the job status.

        Returns
        -------
        a dictionary with a summary (see HTTP docs)
        """

        response = requests.get(
            self.url,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        if response.ok:
            return response.json()
        else:
            raise Exception("error fetching status: " + response.text)
        
    def wait(self, sleep_time=60):

        status = self.status()
        n_jobs = status['n_jobs']

        with tqdm(total=n_jobs) as pbar:
            status = self.status()
            completed = status['submitted_jobs']['SUCCEEDED'] + status['submitted_jobs']['FAILED']
                
            while completed < n_jobs:
                time.sleep(sleep_time)

                status = self.status()
                completed = status['submitted_jobs']['SUCCEEDED'] + status['submitted_jobs']['FAILED']
                
                pbar.update(completed)
                



class Job:
    """Class for interacting with a Job
    
    Attributes
    ----------
    batch : Batch
        Parent batch for this job
    id : string
        unique ID of the tool
    url : string
        API endpoint for this tool
    """

    def __init__(self, batch_id, job_id):
        """
        Parameters
        ----------
        batch_id : string
            unique ID of the parent batch
        job_id : string
            unique ID of the job to connect to
        """
        self.batch = Batch(batch_id)
        self.id = job_id
        self.url = self.batch.url + "/jobs/" + job_id

    def status(self):
        """
        Describes the status of the job.

        Returns
        -------
        a dictionary of the job status (see HTTP docs)
        
        Raises	
        ------	

        """
        
        response = requests.get(
            self.url,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        if response.ok:
            description = response.json()
            return description
        else:
            raise Exception("error fetching status: " + response.text)