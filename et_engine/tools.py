import shutil
import requests
import json
import os
from .jobs import Batch
from .config import API_ENDPOINT


class MaxRetriesExceededError(Exception):
    pass


def connect(tool_name):
    # Make API call to GET vfs?name={vfs_name}
    #     - NOTE: Use ToolID to call vfs/{vfsID} to build, etc.
    # Create vfs object by preparing the API endpoint

    status = requests.get(
        API_ENDPOINT + "/tools", 
        # params={'name':tool_name},
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
    )
    if status.ok:
        tool_list = status.json()
        for t in tool_list:
            if t[0] == tool_name:
                tool_id = t[1]
                return Tool(tool_id)
        raise Exception("Tool does not exist")
    
    elif status.status_code == 403:
        raise Exception(f'Access to tool "{tool_name}" is forbidden')
    
    elif status.status_code == 401:
        raise Exception(f'Authorization failed')
    
    elif status.status_code == 500:
        raise Exception(f'Something went wrong - check your API key')
    
    else:
        raise Exception(f'Tool "{tool_name}" could not be accessed')


def delete(name):	
    """deletes the specified VFS	
        
    Parameters	
    ----------	
    name : string	
        Name of the VFS to delete	
    """	
    status = requests.delete(	
        API_ENDPOINT + "/tools", 
        params={'name':name},	
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}	
    )	

    if status.ok:
        return status
    else:
        raise Exception('Delete failed')


def create(name, description):	
    """Creates a new Tool	
        
    Parameters	
    ----------	
    name : string	
        Name of the tool	
    description : string	
        Plain text description of the tool	
    Returns	
    -------	
    Tool	
        A Tool object connected to the newly-created tool	
    Raises	
    ------	
    Warnings	
    --------	
    The API works, but the method does not yet return a connected "Tool" object	
    """	

    # API Request	
    status = requests.post(	
        API_ENDPOINT + "/tools",
        data=json.dumps({	
            "name": name,	
            "description": description	
        }), 	
        headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}	
    )

    if status.ok:
        return status
    else:
        raise Exception('Create failed')
       

class Tool:
    """Class for interacting with a Tool
    
    Attributes
    ----------
    session : Session
        authenticated session
    url : string
        VFS API endpoint
    """


    def __init__(self, tool_id) -> None:
        """Creates a new tool object from an existing tool ID

        Parameters
        ----------
        tool_id : string
            id associated with the tool of interest
        client : Client
            base authenticated client containing the active session
        """
        self.tool_id = tool_id
        self.url = API_ENDPOINT + f"/tools/{tool_id}"


    def __call__(self, **kwargs):
        """Makes the object callable like a function
        
        Keyword arguments are passed to the Tool as environment variables
        If *hardware* keyword is provided, then we will create a hardware spec JSON and send it to the tools/execute endpoint so 

        """  

        if "hardware" in kwargs:
            hardware_arg = kwargs.pop("hardware")
            assert isinstance(hardware_arg, Hardware)
            hardware = hardware_arg.to_dict()

        else:
            hardware = Hardware().to_dict()

        data = {
            'fixed_args': kwargs,
            'variable_args': [],
            'hardware': hardware
        }

        response = requests.post(
            self.url, 
            data=json.dumps(data), 
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        if response.ok:
            return Batch(response.text)
        else:
            raise Exception(response.text)
        

    def run_batch(self, fixed_kwargs={}, variable_kwargs=[], hardware=None):
        """Makes the object callable like a function
        
        Keyword arguments are passed to the Tool as environment variables
        If *hardware* keyword is provided, then we will create a hardware spec JSON and send it to the tools/execute endpoint so 

        """  

        data = {
            'fixed_args': fixed_kwargs,
            'variable_args': variable_kwargs
        }

        if hardware is None:
            data['hardware'] = Hardware().to_dict()
        else:
            assert isinstance(hardware, Hardware)
            data['hardware'] = hardware.to_dict()

        response = requests.post(
            self.url, 
            data=json.dumps(data), 
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        if response.ok:
            return Batch(response.text)
        else:
            print(response)
            raise Exception(response.text)
              
        
    def push(self, folder):
        """Update the tool code
        
        The tool folder must contain:
            1. a Dockerfile
            2. a buildspec.yml file

        When pushed, the folder will be zipped and sent to the ET Engine. There, the tool will be built and run in a container.

        Inside the API, we are:
            1. Triggering codebuild
            2. Codebuild is combined with the pre-installations and clean-up commands, and built inside Engine 

        Parameters
        ----------
        folder : string
            Path to a folder containing the tool
        """

        # ZIP folder
        zip_file = f"{folder}.zip"
        shutil.make_archive(folder, 'zip', folder)

        response = requests.put(
            self.url, 
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        presigned_post = json.loads(response.text)
        
        with open(zip_file, 'rb') as f:
            files = {'file': (zip_file, f)}
            upload_response = requests.post(
                presigned_post['url'], 
                data=presigned_post['fields'], 
                files=files
            )
        return upload_response
    

class Hardware:
    def __init__(self, filesystems=[], memory=512, cpu=1):
        """
        Creates a hardware configuration object
        """
        self.filesystems = filesystems
        self.memory = memory
        self.cpu = cpu


    def to_dict(self):
        return {
            'filesystems': [fs.id for fs in self.filesystems],
            'memory': self.memory,
            'cpu': self.cpu
        }


    def to_json(self):
        """
        Converts the class instance to a json string that can be passed to The Engine
        """
        
        return json.dumps(self.to_dict())

