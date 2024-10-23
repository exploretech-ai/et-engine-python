# ET Engine Python SDK

The official SDK for building ET Engine applications. 

| Resource | Link |
|:----|:-----|
| Command-Line Interface (CLI) tool | https://github.com/exploretech-ai/et-engine-cli |
| ET Engine Web App | https://engine.exploretech.ai |
| Comprehensive Documentation | https://docs.exploretech.ai |
| About ExploreTech | https://exploretech.ai |

# Quick Start

First, make sure you have an account on the [ET Engine Web App](https://engine.exploretech.ai) and that you have a valid API key exported to the environment variable `ET_ENGINE_API_KEY`. See the [tutorial](https://docs.exploretech.ai) for more details.

Once you have your API key set, ensure your Python version is >=3.11.9 and install the package using pip.


```bash
pip install et-engine
```

Open up the Python interpreter or create a new script and run the following commands.

```python
import et_engine as et

# Connect to the client
engine = et.Engine()

# Create a filesystem
my_first_filesystem = et.filesystems.create("my-first-filesystem")

# Upload any text file to the filesystem
my_first_filesystem.upload("path/to/local/file.txt", "hello-world.txt")

# Check to see if the "hello-world.txt" file was uploaded
filesystem_contents = my_first_filesystem.ls()
print(filesystem_contents)
```

In your browser nagivate to https://engine.exploretech.ai/filesystems to see your new filesystem with a file named `hello-world.txt`.

# Creating and Running Tools

We suggest you create and push tools using the [ET Engine CLI](https://github.com/exploretech-ai/et-engine-cli). For this section, we'll assume you have created a tool named `hello-world-tool` that takes a `name` argument and writes a text file named `hello.txt` with the contents `f"Hello, {name}"`

```python
import et_engine as et
engine = et.Engine()

# Create and connect to a filesystem
my_filesystem = engine.filesystems.create("hello-world-filesystem")

# Connect to the tool
hello = engine.tools.connect("hello-world-tool")

# Define the hardware connection that lets the tool talk to the filesystem
hello_world_hardware = et.Hardware(filesystem_list=[my_filesystem])

# Run the tool, setting the 'name' argument and connecting to your filesystem
job = hello(name="John", hardware=hello_world_hardware)

# Wait for the job to finish
job.wait()
```
If everything went well, your `hello-world-filesystem` will contain a file named `hello.txt` with the contents `Hello, John!`

# Running a Monte Carlo simulation

Let's assume you have a tool named `navier-stokes-simulation` that performs a complex fluid dynamics simulation, and 100 configuration files in a filesystem named `config/configuration_${i}.txt`. To perform a parallelized Monte Carlo simulation on these 100 configuration files, you can use the `run_batch` feature. An example script might look something like this.

```python
import et_engine as et
engine = et.Engine()

# Connect to your Engine resources
monte_carlo_filesystem = et.filesystems.create("monte-carlo")
navier_stokes = engine.tools.connect("navier-stokes-simulation")

# Run each simulation with 16 vCPU & 64 GB Memory
monte_carlo_hardware = et.Hardware(
    filesystem_list=[
        monte_carlo_filesystem
    ],
    cpu=16,         # vCPU
    memory=64*1024  # MB
)

# Define the configuration files
configuration_files = [f"config/configuration_{i}.txt" for i in range(100)]
monte_carlo_parameters = [{"config": c} for c in configuration_files]

# Launch the Monte Carlo simulation
batch = navier_stokes.run_batch(
    variable_kwargs=monte_carlo_parameters,
    hardware=monte_carlo_hardware
)
batch.wait()
```

# Contributing

We welcome contributions from the community. See `CONTRIBUTING.md` for more details.