import requests
import json
import os
import time
from .config import API_ENDPOINT


def list_batches():
     
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

    response = requests.delete(
        API_ENDPOINT + "/batches",
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
    )
    if not response.ok:
        raise


class Batch:
    def __init__(self, batch_id):
        self.id = batch_id
        self.url = API_ENDPOINT + "/batches/" + batch_id
        
    def list_jobs(self):
        
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

        response = requests.delete(
            self.url,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        if not response.ok:
            raise Exception("error deleting batch: " + response.text)
        
    def status(self):

        response = requests.get(
            self.url,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        if response.ok:
            return response.json()
        else:
            raise Exception("error fetching status: " + response.text)


class Job:

    def __init__(self, batch_id, job_id):
        self.batch = Batch(batch_id)
        self.id = job_id
        self.url = self.batch.url + "/jobs/" + job_id

    def status(self):
        
        response = requests.get(
            self.url,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        if response.ok:
            description = response.json()
            return description
        else:
            raise Exception("error fetching status: " + response.text)