import requests
from time import sleep
import json
from ..storage.filesystem import FileSystem

API_URL = 'https://xmnogdgtx4.execute-api.us-east-2.amazonaws.com/prod/'



class Algorithm:
    def __init__(self, InputDataset, OutputDataset, id = None):
        """
        
        """
        
        # Checks if Storage is type "FileSystem"

        # Checks if InputDataset and OutputDataset are type "Dataset"

        # self.storage = FileSystem()
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

        # resources = {
        #     'file': '/path/to/dummy/file',
        #     'id': self.id
        # }
        x = requests.post(API_URL + f'algorithms/{self.id}/execute')
        print(x.text)

        # print("Returns the API execution message")

    def provision(self, monitor = True):
        """
        Wraps storage and computing backend into JSON format
        Sends JSON config to backend via API
        API provisions the resources from there
        API sends back an ID for the algorithm that can be used to get information on execution, etc.
        """

        # API call to provision resources (start with ONLY single node + storage)

        # print(resources)
        

        print('Provisioning resources')
        response = requests.post(API_URL + f'algorithms/{self.id}/provision')
        

        # Loop that checks status
        if monitor:
            for i in range(20):
                status = requests.get(API_URL + f'algorithms/{self.id}/provision')
                status = status.text[1:-1]

                if status == "ready":
                    print(f"Provisioning complete")
                    break

                if status in ["destroying", "error", "destroyed"]:
                    print(f'error provisioning resources: {status}')
                    break

                sleep(5)

            if i == 20:
                print(f'Timed out after 100 pings: {status}')
        
        return response.text

    def destroy(self):

        resources = {
            'id' : self.id
        }
        # print(resources)
        

        x = requests.post(API_URL + 'destroy', json = resources)
        return x.text

    def build(self, dockerfile, app):

        # presigned url for copying dockerfile & app

        # with open(dockerfile) as f:
        #     dockerfile_contents = f.read()
        # with open(app) as f:
        #     app_contents = f.read()

        resources = {
            'dockerfile': dockerfile,
            'app': app
        }

        response = requests.post(API_URL + f'algorithms/{self.id}/build', json=resources)
        # print(response.text)
        
        dockerile_url = json.loads(response.text)["presignedUrl1"]
        app_url = json.loads(response.text)["presignedUrl2"]
        
        with open(resources["dockerfile"], 'rb') as f:
            files = {'file': (resources["dockerfile"], f)}
            http_response = requests.post(dockerile_url['url'], data=dockerile_url['fields'], files=files)

        with open(resources["app"], 'rb') as f:
            files = {'file': (resources["app"], f)}
            http_response = requests.post(app_url['url'], data=app_url['fields'], files=files)

        return response.text
