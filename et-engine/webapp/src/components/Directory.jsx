import React, {useState, useEffect} from "react";
import './Directory.css'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {faTrash, faDownload, faArrowRight, faFolder} from '@fortawesome/free-solid-svg-icons'

const FileComponent = ({name, path, vfsId, idToken, fetchContents, setLoading}) => {
    
    const downloadItem = async (e) => {
        
        let key
        if (path.length === 1) {
            key = name
        }
        else {
            key = path.slice(1) + "/" + name
        }
        fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs/" + vfsId + "?" + new URLSearchParams({
                key: key
            }),
            {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + idToken
                },
            }
        ).then(response => {
            if (response.ok) {
                return response.json()
            } else {
                return "ERROR"
            }
        }).then(presignedUrl => {

            console.log(presignedUrl)

            fetch(presignedUrl)
            .then(response => {
                if (response.ok) {
                    return response.blob()
                } else {
                    console.log(response)
                    throw new Error('response went wrong')
                }
            })
            .then(blob => {
                
                // Download the file
                const url = URL.createObjectURL(blob);
                const element = document.createElement('a');
                element.setAttribute('href', url);
                element.setAttribute('download', name);

                document.body.appendChild(element);
                
                element.click();
                
                document.body.removeChild(element);
                URL.revokeObjectURL(url);

            })
            .catch(error => console.error(error))

        })
        .catch(error => console.error(error))
    };

    const deleteItem = async (e) => {
        
        let key
        if (path.length === 1) {
            key = name
        }
        else {
            key = path.slice(1) + "/" + name
        }
        console.log('Delete Requested on ', key)
        setLoading(true)

        fetch("https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs/" + vfsId + "/files/" + key, {
            method: "DELETE",
            headers: {
                "Authorization": "Bearer " + idToken
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json()
            } else {
                throw new Error('Delete failed')
            }
        })
        .then(response => {
            setLoading(true)
            fetchContents()
            console.log('success: ',response)
        })
        .catch(error => {
            setLoading(false)
            console.error(error)
        })
    }
    return(
        <div key={name} className="file">
            <FontAwesomeIcon icon={faArrowRight} style={{flex: 1, color: "gray"}}/>
            <a key={name+"-p"} style={{flex: 20}}>{name}</a>
            <FontAwesomeIcon icon={faDownload} style={{flex: 1}} onClick={downloadItem} className="icon"/>
            <FontAwesomeIcon icon={faTrash} className="icon" style={{flex: 1}} onClick={deleteItem}/>
            
        </div>
    )
}

const FolderComponent = ({name, path, setPath, setLoading}) => {

    const handleClick = () => {
        setPath([...path, name])
        setLoading(true)
    }

    return(
        <div key={name} className="folder" onClick={handleClick}>
            <FontAwesomeIcon icon={faFolder} style={{flex: 1, color: "gray"}}/>
            <a key={name+"-p"} style={{flex: 20}}>{name}</a>
        </div>
    )
}

const DirectoryView = ({path, vfsId, setPath, contents, setContents, idToken, setLoading, fetchContents, style}) => {

    const folderList = []
    const components = [] 

    if (contents){
        for (const dir of contents.directories) {
            folderList.push(dir)
        }
        folderList.sort()
        for (const folder of folderList) {
            components.push(
                <FolderComponent 
                    name={folder} 
                    path={path} 
                    setPath={setPath}
                    key={folder}
                    setLoading={setLoading}
                />
            )
        }

        const fileList = []
        for (const file of contents.files) {
            fileList.push(file)
        }
        fileList.sort()
        for (const file of fileList) {
            components.push(
                <FileComponent 
                    name={file} 
                    key={file} 
                    vfsId={vfsId}
                    path={path}
                    idToken={idToken}
                    fetchContents={fetchContents}
                    setLoading={setLoading}
                />
            )
        }
    }

    return(
        <div style={style} className="directory">
            {components}
        </div>
    )
}

const CurrentDirectoryPath = ({path, setPath, setLoading}) => {

    const handleClick = (i) => {
        const newPath = [...path.slice(0, i+1)]
        setPath(newPath);
        setLoading(true)
    }
    const folders = []
    if (path){

        for (let i = 0; i < path.length; i++) {
            const component = path[i]
            folders.push(
                <div key={i} onClick={() => handleClick(i)}>
                    {component + '/'}
                </div>
            )
        }
    }
    
    return (
        <div className="path">
            {folders}
        </div>
    )
}

const Directory = ({style, resource, command, idToken, loading, setLoading, path, setPath}) => {

    const [contents, setContents] = useState(null)

    const fetchContents = () => {
        if (resource && idToken) {
            console.log('Fetching directory contents...')
            fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/" + resource.resource + "/" + resource.id + command + "?" + new URLSearchParams({
                    path: path.join('/')
                }), {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + idToken
                    }
                }
            )
            .then(response => {
                if (response.ok) {
                    return response.json()
                } else {
                    throw new Error('empty directory')
                }
            })
            .then( files => {
                setContents(files)
                setLoading(false)
                console.log('success')
            })
            .catch(err => {
                setLoading(false)
                console.log(err)
            })
        }
    }

    useEffect(() => {
        fetchContents()
    }, [resource, path])

    return(
        <div style={style} className="directory-container">
            <CurrentDirectoryPath 
                path={path} 
                setPath={setPath}
                contents={contents}
                setContents={setContents}
                setLoading={setLoading}
            />
            {loading ?
                <div> Loading contents... </div>
            :
                <DirectoryView 
                    path={path} 
                    setPath={setPath}
                    contents={contents}
                    setContents={setContents}
                    vfsId={resource.id}
                    idToken={idToken}
                    setLoading={setLoading}
                    fetchContents={fetchContents}
                />
            }
        </div>
        
    )
}

export default Directory