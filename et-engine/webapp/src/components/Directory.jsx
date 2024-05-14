import React, {useState, useEffect} from "react";
import './Directory.css'


const FileComponent = ({name}) => {
    return(
        <div key={name} className="file">
            {name}
        </div>
    )
}

const FolderComponent = ({name, path, setPath}) => {

    const handleClick = () => {
        // setCurrentDirectory(directory)
        // console.log()
        setPath([...path, name])
    }

    return(
        <div key={name} className="folder" onClick={handleClick}>
            <a key={name+"-p"}>{name}</a>
        </div>
    )
}

const DirectoryView = ({path, setPath, contents, setContents, style}) => {

    const components = []

    if (contents){
        for (const dir of contents.directories) {
            components.push(
                <FolderComponent 
                    name={dir} 
                    path={path} 
                    setPath={setPath}
                    key={dir}
                />)
        }
        for (const file of contents.files) {
            components.push(<FileComponent name={file} key={file}/>)
        }
    }

    

    return(
        <div style={style}>
            {components}
        </div>
    )
}

const CurrentDirectoryPath = ({path, setPath}) => {

    const handleClick = (i) => {

        // 
        const newPath = [...path.slice(0, i+1)]
        setPath(newPath);

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
            {folders}
        </div>
    )
}

const Directory = ({style, resource, command, idToken}) => {

    // const [directory, setDirectory] = useState(null)
    // const [currentDirectory, setCurrentDirectory] = useState(null)
    // const [currentDirectoryPath, setCurrentDirectoryPath] = useState(null)
    const [path, setPath] = useState(['.'])
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
                console.log(files)
                setContents(files)
                // setDirectory(files)
                // setCurrentDirectory(files)
                // setCurrentDirectoryPath(['.'])
            })
            .catch(err => {
                console.log(err)
                // setDirectory(null)
                // setCurrentDirectory(null)
                // setCurrentDirectoryPath(['.'])
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
            />
            <DirectoryView 
                path={path} 
                setPath={setPath}
                contents={contents}
                setContents={setContents}
            />
        </div>
        
    )
}

export default Directory