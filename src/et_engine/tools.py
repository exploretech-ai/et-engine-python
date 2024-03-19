import shutil
import requests
import json

class Tool:

    def __init__(self, tool_id, client) -> None:
        self.session = client.session
        self.url = client.API_ENDPOINT + f"tools/{tool_id}"





    def __call__(self, **kwargs):

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