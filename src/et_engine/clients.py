import requests

API_ENDPOINT = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/"

class Session:

    def __init__(self, credentials):
        
        with open(credentials) as f:
            lines = f.readlines()
            self.user = lines[0]
            self.password = lines[1]

class VirtualFileSystemClient(Session):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def connect(self, name):

        # GET enpoint/vfs
        url = API_ENDPOINT + "vfs"
        status = requests.get(url, params={"name": name}, auth=('user', 'pass'))
        return status
        

    def create(self, name):
        url = API_ENDPOINT + "vfs"
        status = requests.post(url, data={"name": name}, auth=(self.user, self.password))
        return status

    def file_exists(self):
        pass


class ToolsClient(Session):
    
    def create(self):
        pass


class Client(Session):

    def __init__(self, credentials):
        super().__init__(credentials)

        self.vfs = VirtualFileSystemClient(credentials)
        self.tools = ToolsClient(credentials)


