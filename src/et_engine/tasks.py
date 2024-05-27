import requests
import json
import os

API_ENDPOINT = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/"


class Task:
    def __init__(self, task_id):
        self.id = task_id
        self.url = API_ENDPOINT + "/tasks/" + task_id

    def status(self):

        response = requests.get(
            self.url,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        
        if response.ok:
            task_status = response.json()
            return task_status
        else:
            raise Exception('error fetching status')