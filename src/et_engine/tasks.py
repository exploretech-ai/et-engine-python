import requests
import json
import os
import time


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
        
    def wait(self, frequency=60, max_tries=100):
        for i in range(max_tries):
            status = self.status()
            print(status)
            if status == "STOPPED":
                print("task finished")
                break
            time.sleep(frequency)
