import shutil
import requests
import json
import os
from .jobs import Batch
from .config import API_ENDPOINT


class MaxRetriesExceededError(Exception):
    pass


def connect(tool_name):
    """
    Searches for a tool with the specified name and returns a Tool object if found.

    Parameters	
    ----------	
    name : string	
        Name of the tool to connect to	
    """

    status = requests.get(
        API_ENDPOINT + "/tools", 
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
    id : 
        unique ID of the tool
    url : string
        API endpoint for this tool
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
        self.id = tool_id
        self.url = API_ENDPOINT + f"/tools/{tool_id}"


    def __call__(self, **kwargs):
        """Makes the object callable like a function
        
        Parameters
        ----------
        kwargs : dict
            key-value arguments to be passed into the job. If *hardware* keyword is provided, it must be of type Hardware and it will be used to specify the hardware for the job to run on.
  
        Returns
        -------
        a jobs.Batch object

        Keyword arguments are passed to the Tool as environment variables

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
        """

        Parameters
        ----------
        fixed_kwargs : dict
            key-value arguments to be passed into each job in the batch
        variable_kwargs : [dict]
            variable arguments to be passed into separate jobs in the batch
        hardware : Hardware
            the compute hardware to run for each job in the batch
        
        Returns
        -------
        a jobs.Batch object

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
              
        
    def push(self, tar_gz_file):
        """Update the tool code
        
        Before pushing the tool, you must build, save, and gzip a docker image on your computer. To do this, run the following commands.

        ```
        docker build --tag my_tool /path/to/docker/folder
        docker save my_tool | gzip > my_tool.tar.gz
        ```

        Then, pass the path to `/path/to/my_tool.tar.gz` to this function. The image will be uploaded, processed, and made available for use.

        
        Parameters
        ----------
        tar_gz_file : string
            Path to the `.tar.gz` file containing the image
        """

        if not tar_gz_file.endswith(".tar.gz"):
            raise Exception("File must have .tar.gz")

        response = requests.put(
            self.url, 
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )

        presigned_post = json.loads(response.text)
        
        with open(tar_gz_file, 'rb') as f:
            files = {'file': (tar_gz_file, f)}
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

