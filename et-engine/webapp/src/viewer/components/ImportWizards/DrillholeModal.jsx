import React, {useRef, useContext, useState} from "react"
import { CBContext } from "../../../pages/Viewer";
import './modal.css'
import Drillhole from "../../layers/Drillhole";

/*
This dialog box operates a wizard with 2 pages. The first page lets you upload a file. The second page lets you adjust the import parameters.
*/
function LinesModal({toggleOpen}) {

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
      const file = document.getElementById("newDrillhole").files[0]
      
      // NOTE: THIS IS SUPPOSED TO STOP THIS FUNCTION IF THE USER CANCELS THE FILE UPLOAD BUT DOESNT WORK
      if (file === undefined) {
          return
      }

      const parameters = await importDrillhole(await file.text())
      setParameters(parameters)
      setLayerName(file.name)
      setPage(2)

  }

  return(
    <div>
      <p>Upload a .dh file</p>
      <input 
          type='file' 
          name={"newDrillhole"}
          id={"newDrillhole"}
          ref={inputRef} 
          onChange={async () => await createNew()} 
          onClick={(e) => e.stopPropagation()} // without the stopPropagation the box does not click
          accept={".dh"}
          multiple={false}
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
      await newProps.set(submittedParameters, Drillhole, submittedName)

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
      <input type="submit" onClick={async () => await submitParameters(layerName)}/>
    </div>
  )
}



async function importDrillhole(fileText) {

    // 4. split the text by newline
    let lines = fileText.split("\n");

    // First row is the drillhole parameters
    const drillholeParams = lines.shift().split(" ").map((v) => Number(v))
    const collar = [drillholeParams[0], drillholeParams[1], drillholeParams[2]]
    const dip = drillholeParams[3]
    const dipDirection = drillholeParams[4]

    // Interval array
    const numIntervals = Number(lines.shift())//.map((v) => Number(v))
    const length = drillholeParams[5] * (numIntervals - 1)

    const intervals = []
    for (let i = 0; i < numIntervals; i++) {
        intervals.push(Number(lines.shift()))
    }

    // Observation arrays (e.g. borehole logs)
    const numObservations = Number(lines.shift())
    const observations = []
    for (let i = 0; i < numObservations; i++) {

        const currentObservation = []
        for (let j = 0; j < numIntervals; j++) {
            currentObservation.push(Number(lines.shift()))
        }

        observations.push(currentObservation)
    }
    
    const parameters = {
        numIntervals: numIntervals,
        numObservations: numObservations,
        intervals: intervals,
        observations: observations,
        collar: collar,
        dip: dip,
        dipDirection: dipDirection,
        length: length
    }
    return parameters

}

export default LinesModal
