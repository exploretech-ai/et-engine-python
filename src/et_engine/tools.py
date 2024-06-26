import shutil
import requests
import json
import os
from .tasks import Task
import asyncio, aiohttp
from tqdm import tqdm
import time
from . import API_ENDPOINT

class MaxRetriesExceededError(Exception):
    pass


def connect(tool_name):
    # Make API call to GET vfs?name={vfs_name}
    #     - NOTE: Use ToolID to call vfs/{vfsID} to build, etc.
    # Create vfs object by preparing the API endpoint

    status = requests.get(
            API_ENDPOINT + "tools", 
            params={'name':tool_name},
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
    if status.ok:

        tool_id = status.json()[0][1]
        return Tool(tool_id)
    
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
        API_ENDPOINT + "tools", 
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
        API_ENDPOINT + "tools",
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


def parse_kwargs(**kwargs):
        if kwargs:
            if 'hardware' in kwargs:
                assert isinstance(kwargs['hardware'], Hardware)
                kwargs['hardware'] = kwargs['hardware'].to_dict()

            return json.dumps(kwargs)

        else:
            return None
        

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
        self.url = API_ENDPOINT + f"tools/{tool_id}"


    def __call__(self, **kwargs):
        """Makes the object callable like a function
        
        Keyword arguments are passed to the Tool as environment variables
        If *hardware* keyword is provided, then we will create a hardware spec JSON and send it to the tools/execute endpoint so 

        """  

        n_tries = 0
        while n_tries < 300:
            try:
                task = asyncio.run(self.execute(**kwargs))
                print(f'Successfully launched task {task.id}')
                return task
            
            except Exception as e:
                n_tries += 1
                print(f'Failed attempts: {n_tries}. Waiting 1 minute and trying again...')
                time.sleep(60)

        raise MaxRetriesExceededError(f'failed to execute {n_tries} times')


    async def execute(self, **kwargs):

        # async def make_request():
        data = parse_kwargs(**kwargs)
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, data=data, headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}) as status:
                if status.ok:
                    return Task(await status.json())
                else:
                    print(await status.text())
                    print(kwargs)
                    # return None
                    raise Exception('Execute failed')
            
                

    async def execute_one(self, session, **kwargs):
        data = parse_kwargs(**kwargs)
        async with session.post(self.url, data=data, headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}) as status:
            if status.ok:
                return Task(await status.json())
            else:
                return None
                

    async def parallel(self, kwarg_list):

        async with aiohttp.ClientSession() as session:
            tasks = set()
            for i, kwargs in enumerate(kwarg_list):
                task = asyncio.create_task(self.execute_one(session, **kwargs))
                tasks.add(task)

            results = []
            for t in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                results.append(await t)

        return results


    def monte_carlo(self,kwarg_list):
        task_list = asyncio.run(self.parallel(kwarg_list)) 
        n_fails = 0
        for t in task_list:                
            if t is None:
                n_fails += 1
                task_list.remove(t)
        print(f'Successfully launched {(1 - (n_fails) / len(task_list))*100}% of tasks ({n_fails} failed).')
        return task_list

        





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
        zip_file = f"./{folder}.zip"
        shutil.make_archive(f"./{folder}", 'zip', folder)

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
    def __init__(self, filesystems=[], memory=512, cpu=1, gpu=None):
        """
        Creates a hardware configuration object
        """
        self.filesystems = filesystems
        self.memory = memory
        self.cpu = cpu
        self.gpu = gpu

    def to_dict(self):
        return {
            'filesystems': self.filesystems,
            'memory': self.memory,
            'cpu': self.cpu,
            'gpu': self.gpu
        }

    def to_json(self):
        """
        Converts the class instance to a json string that can be passed to The Engine
        """
        
        return json.dumps(self.to_dict)

