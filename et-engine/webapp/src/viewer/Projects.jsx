import "./Projects.css"
import React, {useContext, useEffect, useRef, useState} from 'react'
import { CBContext } from "../pages/Viewer"


function Projects({ setViewer, setFocus }) {

    // const DemoProject = new Project("Demo Project", "0")
    const createNewProject = () => {
        console.log("new project")
        setViewer(true)
    }
    
    return(
        <div id="projects-container">
            <p style={{fontSize: "40px"}}>Select Project</p>
            <button onClick={createNewProject}>New Project</button>
            <FileUpload setViewer={setViewer} setFocus={setFocus}/>
            
        </div>    
    )
}

function FileUpload({setViewer, setFocus}) {

    const [, checkboxProps, checkboxPropSetters] = useContext(CBContext)
    const [loading, setLoading] = useState(false)

    const uploadRef = useRef(null)

    const loadFile = async () => {
        setLoading(true)

        const file = document.getElementById("loadProject").files[0]

        const text = await file.text();
        const layerProperties = text.split('\n---\n')
        
        for (let i = 0; i < checkboxProps.length; i++) {
            if (layerProperties[i].split('\n').length > 4) {

                const newCB = checkboxProps[i].clone()
                await newCB.setFromFile(layerProperties[i])
                checkboxPropSetters[i](newCB)

            }
        }

        setLoading(false)
        setViewer(true)
    }


    const fileUploadButton = <button onClick={() => uploadRef.current.click()}>Import Project</button>
    
    return(
        <div>
            <input 
                type='file' 
                id='loadProject'
                ref={uploadRef} 
                accept=".project" 
                onChange={loadFile}
                multiple={false}
                style={{display: 'none'}} 
            />
            {loading ? <Loader />:fileUploadButton}
            
        </div>
    )
}


function Loader() {
    return (
        <p>Loading (this may take a few minutes)...</p>
    )
  }

export default Projects