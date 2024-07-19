# Template Contents

1. `efs-basic` is for virtual filesystems
2. `compute-basic` is for the computing
3. `buildspec.yml` is for codebuild projects which run once tools are pushed
4. `update_templates.sh` is used to update all the above templates and push them to s3


# Building tools

Once you've created a Dockerfile inside a folder `/path/to/docker/folder`, you can get the tool on the cloud via the following steps:
```
docker build --tag my_tool /path/to/docker/folder
docker save my_tool | gzip > my_tool.tar.gz
```
Once you've generated `my_tool.tar.gz` you can push to The Engine by opening a Python interpreter and running

```
>>> from et_engine import tools
>>> my_tool = tools.connect("my_tool_name")
>>> my_tool.push("my_tool.tar.gz")
```

If you get a response `204` then your tool has been successfully uploaded and the build will be attempted.

# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
