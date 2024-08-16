import requests
import json
import os
import time
import logging
import sys
from .jobs import Batch
from .config import API_ENDPOINT, MultipartUpload, MIN_CHUNK_SIZE_BYTES


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
              
        
    def status(self):
        response = requests.get(
            self.url,
            headers={"Authorization": os.environ["ET_ENGINE_API_KEY"]}
        )
        if response.ok:
            description = response.json()
            return description
        else:
            raise Exception("error fetching status: " + response.text)
        

    def push(self, tar_gz_file, chunk_size=MIN_CHUNK_SIZE_BYTES, connections=100, wait=False, sleep_time=60):
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
        chunk_zie : int
            Size of the file chunks to be uploaded in bytes, default = 8192 (8MB) (optional)
        """

        if not tar_gz_file.endswith(".tar.gz"):
            raise Exception("File must have .tar.gz")
        
        tool_contents = MultipartUpload(tar_gz_file, self.url, method="PUT", chunk_size=chunk_size, connections=connections)
        tool_contents.request_upload()
        tool_contents.upload()
        tool_contents.complete_upload()

        if wait:
            ready = False
            while not ready:
                time.sleep(sleep_time)
                status = self.status()
                if status["buildStatus"] != "IN_PROGRESS":
                    ready = True
                

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


class Logger:
    """
    Utility for tool-side logging. The determination of whether to log, where to log, and what
    logging level to use must be made within the tool.
    """

    def __init__(self, log_file, level='info'):
        """
        Parameters
        ----------
        log_file : str
            File name for logging. (If a file name with path is provided, remember that this is
            on whatever virtual file system may be set up and mounted with the docker container
            running the tool. Also, note that certain tools are already set up to write these
            log files to specific places in the virtual file system.)
        level : str, optional
            Specified logging level. May be 'debug', 'info', 'warning', 'error', or 'critical'.
            Default 'info'. If `level` is not specified as one of these, then defaults to 'info'.
        """

        if level.lower() == 'debug':
            logging_level = logging.DEBUG
        elif level.lower() == 'info':
            logging_level = logging.INFO
        elif level.lower() == 'warning':
            logging_level = logging.WARNING
        elif level.lower() == 'error':
            logging_level = logging.ERROR
        elif level.lower() == 'critical':
            logging_level = logging.CRITICAL
        else:
            logging_level = logging.INFO

        self.logger = logging.getLogger(__name__)
        log_handler = logging.FileHandler(
            filename=log_file,
            encoding='utf-8'
        )
        logging.basicConfig(handlers=[log_handler], level=logging_level,
                            format='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %I:%M:%S %p')

        # create a handler to pipe all uncaught exceptions to log file
        # https://betterstack.com/community/questions/how-to-log-uncaught-exceptions-in-python/
        def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
            self.logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.excepthook = handle_unhandled_exception

        # ensure that warnings are also logged
        logging.captureWarnings(True)

        # since the python logger appends to existing log file, use this to separate out
        #  subsequent tool runs... makes debugging based on the log file a little easier
        self.info('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        self.info('================================================================================')
        self.info('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        self.info(f'Requested logging at level {level}; logging at level {self.logger.level}')

    def info(self, *args, **kwargs):
        return self.logger.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self.logger.debug(*args, **kwargs)


class Argument:
    """Tool-side argument handling
    """

    def __init__(self, name, type=str, description="", required=False, default=None):
        self.name = name
        self.type = type
        self.description = description
        self.required = required
        self.default = default

    @property
    def value(self):
        if self.required:
            try:
                arg_value = os.environ[self.name]
            except KeyError as e:
                raise Exception(f"Required argument '{self.name}' not found")
        else:
            arg_value = os.environ.get(self.name, default=self.default)

        if arg_value is not None:
            arg_value = self.type(arg_value)

        return arg_value


class ArgParser:
    """Tool-side argument parser
    """

    arguments = []

    def add_argument(self, name, type=str, description="", required=False, default=None):
        arg = Argument(name, type=type, description=description, required=required, default=default)
        self.arguments.append(arg)
        self.__setattr__(arg.name, arg.value)

