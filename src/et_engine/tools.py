import shutil
import requests
import json
import os

API_ENDPOINT = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/"

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
        return status

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

        This API call triggers a SSM command that does:
            1. docker pull <TOOL_IMAGE>     // from ECR
            2. docker run ...

        To trigger the API call, I need to know the instance-id to run something like this

            ssm_client = boto3.client('ssm')
            instance_id = 'your-instance-id'
            docker_command = 'docker run -d your-docker-image'
            
            # Send command to EC2 instance
            response = ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={'commands': [docker_command]},
            )

        The instance_id is provided in the path

        If *hardware* keyword is provided, then we will create a hardware spec JSON and send it to the tools/execute endpoint so 
            

        
        """



        if kwargs:
            data = json.dumps(kwargs)
        else:
            data = None

        # NOTE: see here for asynchronous request sending https://stackoverflow.com/questions/74567219/how-do-i-get-python-to-send-as-many-concurrent-http-requests-as-possible
        response = requests.post(
            self.url, 
            data=data,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        return response


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