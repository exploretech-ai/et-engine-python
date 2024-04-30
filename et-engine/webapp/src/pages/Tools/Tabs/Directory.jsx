import React, {useState, useEffect} from "react";
import './Directory.css'


const FileComponent = ({name}) => {
    return(
        <div key={name} className="file">
            {name}
        </div>
    )
}

const FolderComponent = ({name, directory, setCurrentDirectory, currentDirectoryPath, setCurrentDirectoryPath}) => {

    const handleClick = () => {
        setCurrentDirectory(directory)
        // console.log()
        setCurrentDirectoryPath([...currentDirectoryPath, name])
    }

    return(
        <div key={name} className="folder" onClick={handleClick}>
            <a key={name+"-p"}>{name}</a>
        </div>
    )
}

const DirectoryView = ({currentDirectory, setCurrentDirectory, currentDirectoryPath, setCurrentDirectoryPath, style}) => {

    const components = []
    for(const dir in currentDirectory) {

        if (currentDirectory[dir] === null) {
            components.push(<FileComponent name={dir} key={dir}/>)
        } else {
            components.push(
                <FolderComponent 
                    name={dir} 
                    directory={currentDirectory[dir]} 
                    setCurrentDirectory={setCurrentDirectory} 
                    currentDirectoryPath={currentDirectoryPath} 
                    setCurrentDirectoryPath={setCurrentDirectoryPath}
                    key={dir}
                />)
        }
    }

    return(
        <div style={style}>
            {components}
        </div>
    )
}

const CurrentDirectoryPath = ({path, setPath, directory, setDirectory}) => {

    const folders = []
    if (path){

        for (let i = 0; i < path.length; i++) {
            const component = path[i]
            folders.push(
                <div key={i} onClick={() => {
                    const newPath = [...path.slice(0, i+1)]
                    setPath(newPath);

                    let subfolder = {...directory}
                    for (let i = 1; i < newPath.length; i++){
                        subfolder = subfolder[newPath[i]]
                    }
                    setDirectory(subfolder)
                }}>
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

const Directory = ({style, activeTool, idToken}) => {

    const [directory, setDirectory] = useState(null)
    const [currentDirectory, setCurrentDirectory] = useState(null)
    const [currentDirectoryPath, setCurrentDirectoryPath] = useState(null)

    useEffect(async () => {
        
        // Fetch directory structure here
        if (activeTool && idToken) {
            const files = await fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools/" + activeTool.id + "/code", {
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
                setDirectory(files)
                setCurrentDirectory(files)
                setCurrentDirectoryPath(['.'])
            })
            .catch(err => {
                console.log(err)
                setDirectory(null)
                setCurrentDirectory(null)
                setCurrentDirectoryPath(['.'])
            })
            

        }
    }, [activeTool, idToken])



    return(
        // <div style={style}>Directory will appear here</div>
        <div style={style}>
            <CurrentDirectoryPath 
                path={currentDirectoryPath} 
                setPath={setCurrentDirectoryPath}
                directory={directory}
                setDirectory={setCurrentDirectory}
            />
            <DirectoryView 
                currentDirectory={currentDirectory} 
                setCurrentDirectory={setCurrentDirectory} 
                currentDirectoryPath={currentDirectoryPath}
                setCurrentDirectoryPath={setCurrentDirectoryPath}
            />
        </div>
        
    )
}

export default Directory