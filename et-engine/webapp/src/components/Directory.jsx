import React, {useState, useEffect} from "react";
import './Directory.css'


const FileComponent = ({name, path, vfsId, idToken}) => {
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
    return(
        <div key={name} className="file">
            <i class="fa fa-arrow-right" style={{flex: 1}}></i>
            <a key={name+"-p"} style={{flex: 20}}>{name}</a>
            <span className="download-icon" onClick={downloadItem}>
                <i class="fa fa-download" ></i>
            </span>
            
        </div>
    )
}

const FolderComponent = ({name, path, setPath, setLoading}) => {

    const handleClick = () => {
        // setCurrentDirectory(directory)
        // console.log()
        setPath([...path, name])
        setLoading(true)
    }

    return(
        <div key={name} className="folder" onClick={handleClick}>
            <i class="fa fa-folder" style={{flex: 1}}></i>
            <a key={name+"-p"} style={{flex: 20}}>{name}</a>
        </div>
    )
}

const DirectoryView = ({path, vfsId, setPath, contents, setContents, idToken, setLoading, style}) => {

    const components = []

    if (contents){
        for (const dir of contents.directories) {
            components.push(
                <FolderComponent 
                    name={dir} 
                    path={path} 
                    setPath={setPath}
                    key={dir}
                    setLoading={setLoading}
                />
            )
        }
        for (const file of contents.files) {
            components.push(
                <FileComponent 
                    name={file} 
                    key={file} 
                    vfsId={vfsId}
                    path={path}
                    idToken={idToken}
                />
            )
        }
    }

    

    return(
        <div style={style}>
            {components}
        </div>
    )
}

const CurrentDirectoryPath = ({path, setPath, setLoading}) => {

    const handleClick = (i) => {

        // 
        const newPath = [...path.slice(0, i+1)]
        setPath(newPath);
        setLoading(true)

        // let subfolder = {...directory}
        // for (let i = 1; i < newPath.length; i++){
        //     subfolder = subfolder[newPath[i]]
        // }
        // setDirectory(subfolder)
    }
    const folders = []
    if (path){

        for (let i = 0; i < path.length; i++) {
            const component = path[i]
            folders.push(
                <div key={i} onClick={() => handleClick(i)}>
                    {component + '/'}
                </div>)

        }
    }
    
    return (
        <div className="path">
            {/* <p>Current Directory: </p> */}
            {folders}
        </div>
    )
}

const Directory = ({style, resource, command, idToken, loading, setLoading, path, setPath}) => {

    // const [directory, setDirectory] = useState(null)
    // const [currentDirectory, setCurrentDirectory] = useState(null)
    // const [currentDirectoryPath, setCurrentDirectoryPath] = useState(null)
    
    const [contents, setContents] = useState(null)

    useEffect(async () => {
        
        if (resource && idToken) {
            const searchPath = path.join('/')
            const files = await fetch(
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
                } 
                throw new Error('empty directory')
                
            })
            .then( files => {
                setContents(files)
                setLoading(false)
            })
            .catch(err => {
                setLoading(false)
                console.log(err)
            })
        }
    }, [resource, path])



    return(
        // <div style={style}>Directory will appear here</div>
        <div style={style}>
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
                />
            }
        </div>
        
    )
}

export default Directory