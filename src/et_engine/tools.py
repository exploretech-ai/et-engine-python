import shutil
import requests
import json

class Tool:
    """Class for interacting with a Tool
    
    Attributes
    ----------
    session : Session
        authenticated session
    url : string
        VFS API endpoint
    """


    def __init__(self, tool_id, client) -> None:
        """Creates a new tool object from an existing tool ID

        Parameters
        ----------
        tool_id : string
            id associated with the tool of interest
        client : Client
            base authenticated client containing the active session
        """
        self.session = client.session
        self.url = client.API_ENDPOINT + f"tools/{tool_id}"


    def __call__(self, **kwargs):
        """Makes the object callable like a function
        
        Keyword arguments are passed to the Tool as environment variables
        """

        if kwargs:
            data = json.dumps(kwargs)
        else:
            data = None

        response = requests.post(
            self.url, 
            data=data,
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        return response


    def push(self, folder):
        """Update the tool code
        
        The tool folder must contain:
            1. a Dockerfile
            2. a buildspec.yml file

        When pushed, the folder will be zipped and sent to the ET Engine. There, the tool will be built and run in a container.

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
            headers={"Authorization": f"Bearer {self.session.id_token}"}
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