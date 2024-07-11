import requests
import json
import os
import time
from .config import API_ENDPOINT

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
            return response.json()
        else:
            print(response)
            raise Exception

        
    def wait(self, sleep=60, n=100):
        """waits for the task to finish
        
        Sends out an API request every `sleep_interval` seconds, up to `max_tries` requests.


        """
        for i in range(n):
            status = self.status()
            print(status)
            if status['status'] == "STOPPED":
                print("task finished")
                return status
            time.sleep(sleep)


        raise Exception('max tries exceeded')


def wait(tasks, n=150, sleep=120):
    """ Monitors a list of tasks
    
    Parameters
    ----------
    n_tries: int
        number of times to call status before timeout (default=150)
    sleep_interval: float
        number of seconds to wait between calling for status (default=120)
    """

    stopped_tasks = []

    for i in range(n):
        stopped_count = len(stopped_tasks)
        running_count = 0

        task_status = {}
        for task in [t for t in tasks if t.id not in stopped_tasks]:
            status = task.status()
            if status['status'] == "STOPPED":

                task_status[task.id] = 'no exit code or reason'
                if status["code"] != -1:
                    task_status[task.id] = f'exit code: {status["code"]}'
                if status["reason"] is not None:
                    task_status[task.id] = f'exit reason: {status["reason"]}'

                stopped_tasks.append(task.id)
                stopped_count += 1

            if status['status'] == "RUNNING":
                running_count += 1
        
        print(f'running: {running_count}, stopped: {stopped_count} (out of {len(tasks)})')
        if stopped_count == len(tasks):
            
            for task_id in task_status.keys():
                print(f'Task {task_id}', task_status[task_id])
            return task_status

        time.sleep(sleep)
    raise Exception('max retries exceeded')

   