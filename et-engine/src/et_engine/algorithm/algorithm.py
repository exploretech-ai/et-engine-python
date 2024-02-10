import requests
from time import sleep
import json

API_URL = 'https://xmnogdgtx4.execute-api.us-east-2.amazonaws.com/prod/'



class BaseAlgorithm:
    def __init__(self, Storage, InputDataset, OutputDataset, id = None):
        """
        
        """
        
        # Checks if Storage is type "FileSystem"

        # Checks if InputDataset and OutputDataset are type "Dataset"

        self.storage = Storage
        self.InputType = InputDataset
        self.OutputType = OutputDataset
        
        if id is None:
            response = requests.post(API_URL + "algorithms")
            self.id = response.text[1:-1]

        else:
            self.id = id
            # self.connect(self.id)

        
        

    def connect(self):
        return self

    def run(self):
        """MUST BE WRITTEN BY USER"""
        pass

    def __call__(self, InputDataset):
        """Wraps around self.run but with checks"""
        
        # print("Writes InputDataset to backend, via API")
        # API call for pushing data here...

        # print("Executing self.run on the backend, via API ")
        # API call for executing here here

        resources = {
            'file': '/path/to/dummy/file',
            'id': self.id
        }
        x = requests.post(API_URL + 'execute', json = resources)
        print(x.text)

        # print("Returns the API execution message")

    def provision(self, storage, compute, monitor = True):
        """
        Wraps storage and computing backend into JSON format
        Sends JSON config to backend via API
        API provisions the resources from there
        API sends back an ID for the algorithm that can be used to get information on execution, etc.
        """

        # API call to provision resources (start with ONLY single node + storage)

        resources = compute.provision()
        # print(resources)
        

        print('Provisioning resources')
        x = requests.post(API_URL + 'provision', json = resources)
        self.id = x.text[5:-1]
        

        # Loop that checks status
        if monitor:
            for i in range(20):
                y = requests.get(API_URL + f'status?id={self.id}')
                y = json.loads(y.text)

                if y['message'] == "ready":
                    print(f"Provisioning complete ({i}s)")
                    break

                if y['message'] in ["destroying", "error", "destroyed"]:
                    print(f'error provisioning resources: {y}')
                    break

                sleep(5)

            if i == 20:
                print(f'Timed out after 100 pings: {y["message"]}')
        
        return self.id

    def destroy(self):

        resources = {
            'id' : self.id
        }
        # print(resources)
        

        x = requests.post(API_URL + 'destroy', json = resources)
        return x.text

    def configure(self, storage, compute):
        resources = compute.provision()
        resources["id"] = self.id
        z = requests.post(API_URL + 'configure', json = resources)
        return z.text
