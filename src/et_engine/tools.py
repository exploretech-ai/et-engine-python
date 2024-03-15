import shutil
import requests
import json

class Tool:

    def __init__(self, tool_id, session) -> None:
        self.session = session
        self.url = session.API_ENDPOINT + f"tools/{tool_id}"

    def __call__(self, **kwargs):
        pass

    def push(self, folder):

        # ZIP folder
        zip_file = f"./{folder}.zip"
        shutil.make_archive(f"./{folder}", 'zip', folder)

        response = requests.post(
            self.url, 
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        return response
        presigned_post = json.loads(response.text)
        return presigned_post
        
        with open(zip_file, 'rb') as f:
            files = {'file': (zip_file, f)}
            upload_response = requests.post(
                presigned_post['url'], 
                data=presigned_post['fields'], 
                files=files
            )
        return upload_response