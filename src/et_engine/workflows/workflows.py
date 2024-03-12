import requests
from time import sleep
import json
from ..storage.filesystem import FileSystem

API_URL = 'https://gsgj2z3zpj.execute-api.us-east-2.amazonaws.com/prod/'


class Module:
    """
    Each Module must have the following arguments:

    type (str): the type of compute stack (options: parallel, if, gpu, bigmem, cpu)
    connections (list of str): string id of modules that are output connections to the module
    config: (dict): key-value pairs of compute stack configuration parameters
    args: (dict): key-value pairs of arguments, where keys are the argument name and values are the expected argument type (string, path, or directory)

    """
    def __init__(self, module_name, module_type, connections, config, args) -> None:
        self.name = module_name
        self.params = {
            "type": module_type,
            "connections": connections,
            "config": config,
            "args": args
        }

class ParallelComputeNode(Module):
    type = "parallel"

    def __init__(self, module_name, output_connection, config, args) -> None:
        super().__init__(module_name, self.type, [output_connection], config, args)


class BigMemNode(Module):
    pass

class GPUNode(Module):
    pass

class IfStatementNode(Module):
    pass

 


class START(Module):
    def __init__(self) -> None:
        super().__init__("START")


class END(Module):
    def __init__(self) -> None:
        super().__init__("END")


class Workflow:
    nodes = []
    edges = {}

    def __init__(self, name = None, id = None):
        """
        
        """
        self.name = name     
        self.id = id   
        

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
        x = requests.post(API_URL + f'users/0/workflows/{self.id}/execute')
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
        response = requests.post(API_URL + f'users/0/workflows/{self.id}/provision')
        

        # Loop that checks status
        if monitor:
            for i in range(20):
                status = requests.get(API_URL + f'users/0/workflows/{self.id}/provision')
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

        x = requests.post(API_URL + f'users/0/workflows/{self.id}/destroy')
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

        response = requests.post(API_URL + f'users/0/workflows/{self.id}/build', json=resources)
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
    
    def add_module(self, module, connection = None):
        self.nodes.append(module)

        edge_id = module.name + "->" + connection.name
        self.edges[edge_id] = {
            "source": module.name,
            "target": connection.name
        }

    def submit(self):
        response = requests.post(API_URL + f'users/0/workflows/{self.id}/submit', json=self.graph)
        return response

    @property
    def graph(self):
        """
        Goes through self.modules in order. First item in the array is the START. 

        Example of the data structure for a 2-node linear directed graph:

        {
            nodes: {
                "START" : None,
                "<node_id1>": {parameters},
                "<node_id2>": {parameters},
                "END": None
            },
            edges: {
                "<edge_id1>": {
                    "source": "START",
                    "target": <node_id1>
                },
                "<edge_id2>": {
                    "source": <node_id1>,
                    "target": <node_id2>
                },
                "<edge_id3>": {
                    "source": <node_id2>,
                    "target": "END"
                }
            }
        }
        """

        # loop through self.nodes and add them to a "nodes" dict
        node_dict = {
            "START": None
        }
        for node in self.nodes:
            node_dict[node.name] = node.params

        node_dict["END"] = None

        self.edges["START->" + self.nodes[0].name] = {
            "source": "START",
            "target": self.nodes[0].name
        }

        # create a "graph" dict with keys "nodes" and "edges"
        return {
            "nodes": node_dict,
            "edges": self.edges
        }


