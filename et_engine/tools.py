import os
import logging
import sys
from typing import Self
import et_engine_core as etc

from . import clients
from .batches import Batch
from .filesystems import Filesystem


class Hardware(etc.Hardware):
    """Interface for defining ET Engine Hardware specs.
    """

    def __init__(self, filesystem_list: list[Filesystem] = [], cpu: int = 1, memory: int = 256):
        """Create an ET Engine Hardware object.

        Args:
            filesystem_list (list[Filesystem], optional): List of filesystems to give jobs access to. Defaults to [].
            cpu (int, optional): Number of processors to give jobs access to, in vCPU. Defaults to 1.
            memory (int, optional): Amount of memory (RAM) to give jobs access to, in MB. Defaults to 256.
        """
        super().__init__(filesystem_list, cpu, memory)


class Tool(etc.Tool):
    """Client for interacting with a specific tool.
    """

    def __init__(self, base_url: str, *args, **kwargs) -> None:
        """Create an interactive ET Engine Tool object.

        Args:
            base_url (str): Base endpoint for requests.
        """
        super().__init__(*args, **kwargs)
        self.client = clients.APIClient(f"{base_url}/tools/{self.tool_id}")
        self.base_url = base_url


    def __call__(self, **kwargs) -> Batch:
        """Makes the object callable like a function.

        Returns:
            Batch: the batch of jobs submitted to The Engine.
        """       

        if "hardware" in kwargs:
            hardware_arg = kwargs.pop("hardware")
            assert isinstance(hardware_arg, Hardware)
            hardware = hardware_arg.to_json()

        else:
            hardware = Hardware().to_json()

        data = {
            'fixed_args': kwargs,
            'variable_args': [],
            'hardware': hardware
        }
        batch_json = self.client.post(data=data)
        return Batch.from_json(self.base_url, batch_json)
        

    def run_batch(self, fixed_kwargs: dict = {}, variable_kwargs: list[dict] = [], hardware: Hardware = Hardware()) -> Batch:
        """Submits a parallelized batch of jobs.

        Args:
            fixed_kwargs (dict, optional): Key-value arguments to be passed into each job in the batch. Defaults to {}.
            variable_kwargs (list, optional): Variable arguments to be passed into separate jobs in the batch. Defaults to [].
            hardware (Hardware, optional): The compute hardware to run for each job in the batch. Defaults to default hardware.

        Returns:
            Batch: The batch of jobs submitted to The Engine
        """
        

        data = {
            'fixed_args': fixed_kwargs,
            'variable_args': variable_kwargs
        }

        if hardware is None:
            data['hardware'] = Hardware().to_json()
        else:
            assert isinstance(hardware, Hardware)
            data['hardware'] = hardware.to_json()

        batch_json = self.client.post(data=data)
        return Batch.from_json(self.base_url, batch_json)
              
        
    def status(self) -> dict:
        """Fetches the current status of the tool.

        Returns:
            dict: A JSON-like dictionary describing the tool status.
        """
        return self.client.get()
    

    def delete(self) -> None:
        """Deletes the tool [NOTE: This action cannot be un-done!]
        """
        return self.client.delete()
    

    @staticmethod
    def from_json(base_url: str, tool_json: dict) -> Self:
        """Convert a JSON object to an interactive Tool.

        Args:
            base_url (str): Base endpoint for requests.
            tool_json (dict): JSON description of the tool.

        Returns:
            Self: A Tool object.
        """
        return Tool(base_url, **tool_json)
                

class Logger:
    """
    Utility for tool-side logging. The determination of whether to log, where to log, and what
    logging level to use must be made within the tool.

    NOTE: This will likely be refactored to another module or repository in the future.
    """

    def __init__(self, log_file: str, level='info', append=True):
        """Creates a logger object.

        Args:
            log_file (str): Path to the log file.
            level (str, optional): Log level, options are ['debug', 'info', 'warning', 'error', 'critical']. Defaults to 'info'.
            append (bool, optional): Whether to append to an existing log or overwrite. Defaults to True.
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

        if append:
            filemode = 'a'
        else:
            filemode = 'w'

        self.logger = logging.getLogger(__name__)
        log_handler = logging.FileHandler(
            filename=log_file,
            encoding='utf-8',
            mode=filemode
        )
        logging.basicConfig(
            handlers=[log_handler], 
            level=logging_level,
            format='%(asctime)s %(message)s',
            datefmt='%Y-%m-%d %I:%M:%S %p'
        )

        def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
            self.logger.critical("UNHANDLED EXCEPTION", exc_info=(exc_type, exc_value, exc_traceback))

        sys.excepthook = handle_unhandled_exception

        logging.captureWarnings(True)

        self.info(f'Requested logging at level {level}; \nlogging at level {logging.getLevelName(self.logger.getEffectiveLevel())}')


    def info(self, *args, **kwargs) -> None:
        """Wrapper around the base logging.info() method.
        """
        self.logger.info(*args, **kwargs)


    def debug(self, *args, **kwargs) -> None:
        """Wrapper around the base logging.debug method.
        """
        self.logger.debug(*args, **kwargs)


class Argument:
    """Tool-side argument handling.

    NOTE: This will likely be refactored to another module or repository in the future.
    """

    def __init__(self, name: str, type: type = str, description: str = "", required: bool = False, default: object = None) -> None:
        """Creates a new Argument to be parsed by the tool.

        Args:
            name (str): Name/key of the argument.
            type (type, optional): Object type of the argument. Defaults to str.
            description (str, optional): Description of the argument. Defaults to "".
            required (bool, optional): Whether the argument is required or not. Defaults to False.
            default (object, optional): Default value of the argument. Defaults to None.
        """
        self.name = name
        self.type = type
        self.description = description
        self.required = required
        self.default = default


    @property
    def value(self) -> object:
        """Sets the value of this argument.

        Raises:
            Exception: If the argument is required but not found in the environment variables.

        Returns:
            object: The argument value.
        """
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
    """Tool-side argument parser.
    """

    def __init__(self, name: str = "") -> None:
        """Creates a new collection of arguments to be parsed.

        Args:
            name (str, optional): name of the parser. Defaults to "".
        """
        self.name = name
        self.arguments = []


    def add_argument(self, name: str, type: type = str, description: str = "", required: bool = False, default: object = None) -> None:
        """Adds an argument to the parser.

        Args:
            name (str): Name/key of the argument.
            type (type, optional): Object type of the argument. Defaults to str.
            description (str, optional): Description of the argument. Defaults to "".
            required (bool, optional): Whether the argument is required or not. Defaults to False.
            default (object, optional): Default value of the argument. Defaults to None.
        """
        arg = Argument(name, type=type, description=description, required=required, default=default)
        self.arguments.append(arg)
        self.__setattr__(arg.name, arg.value)


    def __str__(self) -> str:
        """Prints a summary of the arguments and their values.

        Returns:
            str: A multi-line string representation of the arguments and their values.
        """
        output_string = f"-----{self.name}-----\n"
        for arg in self.arguments:
            output_string += f"{arg.name}: {arg.value}\n"
        output_string += "-" * (10 + len(self.name))
        return output_string


class ToolsClient(clients.APIClient):
    """Client for interacting with ET Engine Tools.
    """

    def __init__(self, base_url: str = clients.DEFAULT_BASE_URL) -> None:
        """Create a new client for interacting with ET Engine Tools.

        Args:
            base_url (str, optional): Base endpoint for requests. Defaults to clients.DEFAULT_BASE_URL.
        """
        super().__init__(f"{base_url}/tools")
        self.base_url = base_url


    def create_tool(self, tool_name: str, tool_description: str) -> Tool:
        """Create a new ET Engine Tool.

        Args:
            tool_name (str): Unique name of the tool.
            tool_description (str): Description of what the tool does.

        Returns:
            Tool: A client for the newly-created Tool.
        """
        data = {
            "tool_name": tool_name,
            "tool_description": tool_description
        }
        tool_json = self.post(data=data)
        return Tool.from_json(self.base_url, tool_json)
    

    def list_tools(self) -> list[Tool]:
        """Lists all the available tools.

        Returns:
            list[Tool]: A list of individual Tool clients.
        """
        tools_list = self.get()
        return [Tool.from_json(self.base_url, t) for t in tools_list]
    

    def connect(self, tool_name: str) -> Tool:
        """Connect to a specific Tool.

        Args:
            tool_name (str): Name of the Tool to connect to.

        Raises:
            Exception: No Tool exists with the specified name.

        Returns:
            Tool: A new Tool client.
        """
        tools_list = self.list_tools()
        for t in tools_list:
            if t.tool_name == tool_name:
                return t
        raise Exception("Tool does not exist")