import et_engine as et


tool = et.tools.delete('MonteCarlo')

    # When you do "vfs.connect(<VFS_NAME>)", the API will need to perform:
    #     * Check whether the API Key has access to the VFS
    #     = IF vfs.connect() comes from a tool, then mount the VFS
    #         -> This is done by running 'sudo mount -t nfs4 <FILE_SYSTEM_DNS>:/ <MOUNT_POINT>'
    #         -> Then, VFS.upload() and VFS.download() are just references to <MOUNT_POINT> ---- vfs.download('local_file', 'vfs_file') adds the file to the Tool's filesystem catalog
    #         -> A tool's filesystem catalog is managed by Python such that
    #              - when vfs.file('vfs_file') is called, it returns the full path where the filesystem is mounted
    #         -> AFTER the tool completes, the VFS in un-mounted
    #     = ELSE all you get is the API ID
    #      

"""
A simple way to test if the "NEW API" is working, is by running something like:


tool = et.tools.connect(hello_world_tool)
tool.push('path/to/tool/directory')
tool(foo='bar') # <-- this just prints "hello, world" in the cloudwatch logs

# now let's test the vfs

vfs = et.vfs.connect(my_vfs)
vfs.upload('local', 'remote')
vfs.download('remote','local_copy')


# now let's test the vfs on EC2
tool(file='path/to/vfs/file') # <-- now, the tool creates this file with "hello, world". the default hardware is t2.micro
vfs.download('path/to/vfs/file', 'local_copy')


# eventually, this lets me run things like this:
tool(file='path/to/file', hardware='aws_instance_name')
# In the backend, the API triggers the provisioning an EC2 resource, installing ET software, and then running the tool docker image
# In the future, I'll have the resources already prepared so connection is fast

# If I'm able to reliably do this, then I can work on writing xFlare



"""




    



        

