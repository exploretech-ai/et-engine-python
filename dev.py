import et_engine as et


if __name__ == "__main__":   
    # Tools and VFS can only be created with OAuth tokens (website)
    # Connecting and moving data on VFS can be done by API Key

    # vfs = et.vfs.connect('test_vfs')
    # print(vfs)

    # vfs.download('my_test.txt', 'downloaded_file.txt')

    tool = et.tools.connect('MonteCarlo')
    print(tool)
    # print(vfs.request.path_url)
    # print(vfs.reason)
    # print(vfs.json())
    # print(vfs.url)
    # print(vfs.text)
    
    
    



        

