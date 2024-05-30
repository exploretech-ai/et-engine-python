import React, {useRef, useContext, useState} from "react"
import { CBContext } from "../../../pages/Viewer";
import './modal.css'
import Ensemble from "../../layers/Ensemble";
import { importVolume } from "./VolumeModal";
/*
This dialog box operates a wizard with 2 pages. The first page lets you upload a file. The second page lets you adjust the import parameters.
*/
function EnsembleModal({toggleOpen}) {

  const [page, setPage] = useState(1)
  const [layerName, setLayerName] = useState(null)
  const [parameters, setParameters] = useState(null)

  function getPage(pageNumber) {
    switch(pageNumber) {
      case 1: 
        return <Page1 setPage={setPage} setParameters={setParameters} setLayerName={setLayerName}/>
      case 2: 
        return <Page2 parameters={parameters} toggleOpen={toggleOpen} layerName={layerName} setLayerName={setLayerName}/>
      default:
        return null
    }
  }
  

  return(
    <div>
      {getPage(page)}
    </div>
    )
}

function Page1({setPage, setParameters, setLayerName}) {
  const inputRef = useRef(null)
  

    
  const createNew = async () => {
      // Load the file & eturn with nothing if the file is empty
      const files = document.getElementById("newEnsemble").files
      
      // NOTE: THIS IS SUPPOSED TO STOP THIS FUNCTION IF THE USER CANCELS THE FILE UPLOAD BUT DOESNT WORK
      if (files === undefined) {
          return
      }

      const parameters = await importEnsemble(files)
      setParameters(parameters)
      setLayerName("New Ensemble")
      setPage(2)

  }

  return(
    <div>
      <p>Select multiple .mesh files that together form an ensemble of realizations.</p>
      <input 
          type='file' 
          name={"newEnsemble"}
          id={"newEnsemble"}
          ref={inputRef} 
          onChange={async () => await createNew()} 
          onClick={(e) => e.stopPropagation()} // without the stopPropagation the box does not click
          accept={".mesh"}
          multiple={true}
      />
    </div>
  )
}
function Page2({parameters, layerName, setLayerName, toggleOpen}) {
  const [, checkboxProps, checkboxPropSetters] = useContext(CBContext)


  async function submitParameters() {
    const newParameters = {...parameters}
    await addCheckbox(newParameters, layerName)
  }

  async function addCheckbox(submittedParameters, submittedName) {
    
      // Get the first checkbox where the new scene will go
      function getFirstAvailable() {
          const maxCheckboxes = checkboxProps.length
          for (let i=0; i<maxCheckboxes; i++) {
              if (!checkboxProps[i].visible) {
                  return i
              }
          }
      }
      const i = getFirstAvailable()
      const props = checkboxProps[i]

      // Update the props for this checkbox
      let newProps = props.clone()
      await newProps.set(submittedParameters, Ensemble, submittedName)

      // Set the new checkbox props and trigger the re-render
      checkboxPropSetters[i](newProps)

      toggleOpen()
  }
        

  return(
    <div>
      <form>
        <label htmlFor="layerNameInput">Layer Name</label>
        <input type="text" id="layerNameInput" value={layerName} onChange={(e) => setLayerName(e.target.value)}/><br/>
      </form>
      <input type="submit" onClick={async () => await submitParameters()}/>
    </div>
  )
}



async function importEnsemble(files) {
    // This global parameter will be used in the loop
    const numRealizations = files.length

    // Holds all the meshes and geometries
    const realizationParameters = []
    const fileNames = []

    // Loop through all the files and load them as MultiVolume objects
    for (let i = 0; i < numRealizations; i++) {

        const parameters = await importVolume(await files[i].text())
        realizationParameters.push(parameters)
        fileNames.push(files[i].name)

    }

    const parameters = {
        realizationParameters: realizationParameters,
        fileNames: fileNames
    }

    return parameters
}


export default EnsembleModal
