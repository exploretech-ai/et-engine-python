import requests
import json
import os

API_ENDPOINT = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/"


def connect(vfs_name):
    # How to know whether the request is from a Tool or not?
    #     - 
    # IF it's from a Tool, then fetch the filesystem DNS from the api
    #    - next, run something like 'sudo mount -t nfs4 <FILE_SYSTEM_DNS>:/ <DEFAULT_MOUNT_POINT>'
    #    - When you call vfs.file('file_name'), it returns <DEFAULT_MOUNT_POINT>/$file_name
    # 

    # ================================================================================
    # =========================== IF DEVICE IS NOT TOOL ==============================
    status = requests.get(
            API_ENDPOINT + "vfs", 
            params={'name':vfs_name},
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
    if status.ok:

        vfs_id = status.json()[0][1]
        return VirtualFileSystem(vfs_id)
    
    else:
        print(status)
        print(status.reason)
        raise NameError(f'Filesystem "{vfs_name}" does not exist')
    # =========================== IF DEVICE IS NOT TOOL ==============================
    # ================================================================================
    

    # ================================================================================
    # ============================= IF DEVICE IS TOOL ================================

    # self.get_dns()       # <-- calls the api and fetches the dns name from the requested vfs name
    # self.mount(self.dns) # <-- runs something like 'sudo mount -t nfs4 <FILE_SYSTEM_DNS>:/ <DEFAULT_MOUNT_POINT>'
    # now, you can access files by writing vfs.file('file_name')

    # ============================= IF DEVICE IS TOOL ================================
    # ================================================================================
    

def list():
    pass


class VirtualFileSystem:
    """Object for interacting with the ET Engine VFS API
    
    Attributes
    ----------
    session : Session
        authenticated session
    url : string
        VFS API endpoint
    """

    def __init__(self, vfs_id):
        """Creates a new object connected to the VFS
        
        Parameters
        ----------
        vfs_id : string
            id associated with the VFS of interest
        """
        self.url = API_ENDPOINT + f"vfs/{vfs_id}"

    def file_exists(self):
        pass

    def upload(self, local_file, remote_file):
        """Uploads a file to the VFS

        Parameters
        ----------
        local_file : string
            path to the local copy of the file to upload
        remote_file : string
            path to the remote copy of the uploaded file inside the VFS

        
        """
        response = requests.post(
            self.url, 
            data=json.dumps({"key": remote_file}),
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        response.raise_for_status()
        presigned_post = json.loads(response.text)
        # print(presigned_post)
        
        with open(local_file, 'rb') as f:
            files = {'file': (local_file, f)}
            upload_response = requests.post(
                presigned_post['url'], 
                data=presigned_post['fields'], 
                files=files
            )

        return upload_response
    
    def download(self, remote_file, local_file):
        """Downloads a copy of a VFS file to the local machine

        Parameters
        ----------
        remote_file : string
            path to the remote copy of the file inside the VFS
        local_file : string
            path to the destination of the downloaded file
        
        """
        response = requests.get(
            self.url, 
            params={"key": remote_file},
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        presigned_url = json.loads(response.text)
        
        with requests.get(presigned_url, stream=True) as r:
            # r.raise_for_status()
            with open(local_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=None):
                    f.write(chunk)

