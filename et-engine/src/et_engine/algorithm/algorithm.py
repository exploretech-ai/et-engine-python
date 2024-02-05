import requests

class BaseAlgorithm:
    def __init__(self, Storage, InputDataset, OutputDataset):
        """
        
        """
        
        # Checks if Storage is type "FileSystem"

        # Checks if InputDataset and OutputDataset are type "Dataset"

        self.storage = Storage
        self.InputType = InputDataset
        self.OutputType = OutputDataset

    def run(self):
        """MUST BE WRITTEN BY USER"""
        pass


    def __call__(self, InputDataset):
        """Wraps around self.run but with checks"""
        
        print("Writes InputDataset to backend, via API")
        # API call for pushing data here...

        print("Executing self.run on the backend, via API ")
        # API call for executing here here

        print("Returns the API execution message")

    def provision(self, storage, compute):
        """
        Wraps storage and computing backend into JSON format
        Sends JSON config to backend via API
        API provisions the resources from there
        API sends back an ID for the algorithm that can be used to get information on execution, etc.
        """

        # API call to provision resources (start with ONLY single node + storage)

        resources = {
            'storage': 'new',
            'compute': 'SingleNode'
        }
        print(resources)
        url = 'https://y0x4jkatv9.execute-api.us-east-2.amazonaws.com/prod/provision'

        x = requests.post(url, json = resources)
        print(x.text)
        


