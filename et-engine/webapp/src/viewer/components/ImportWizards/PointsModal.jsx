import React, {useRef, useContext, useState} from "react"
import { CBContext } from "../../../pages/Viewer";
import './modal.css'
import Points from "../../layers/Points";

/*
This dialog box operates a wizard with 2 pages. The first page lets you upload a file. The second page lets you adjust the import parameters.
*/
function PointsModal({toggleOpen}) {

  const [page, setPage] = useState(1)
  const [layerName, setLayerName] = useState(null)
  const [parameters, setParameters] = useState(null)

  function getPage(pageNumber) {
    switch(pageNumber) {
      case 1: 
        return <Page1 
            setPage={setPage} 
            setParameters={setParameters} 
            setLayerName={setLayerName}
        />
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
      const file = document.getElementById("newPoints").files[0]
      
      // NOTE: THIS IS SUPPOSED TO STOP THIS FUNCTION IF THE USER CANCELS THE FILE UPLOAD BUT DOESNT WORK
      if (file === undefined) {
          return
      }

      const parameters = await importPoints(await file.text())
      setParameters(parameters)
      setLayerName(file.name)
      setPage(2)
  }

  return(
    <div>
      <p>Select a CSV with X, Y, and Z columns in cartesian coordinates.</p>
      <input 
          type='file' 
          name={"newPoints"}
          id={"newPoints"}
          ref={inputRef} 
          onChange={async () => await createNew()} 
          onClick={(e) => e.stopPropagation()} // without the stopPropagation the box does not click
          multiple={false}
      />
    </div>
  )
}
function Page2({parameters, layerName, setLayerName, toggleOpen}) {
  const [, checkboxProps, checkboxPropSetters] = useContext(CBContext)
  const [xColumn, setXColumn] = useState("")
  const [yColumn, setYColumn] = useState("")
  const [zColumn, setZColumn] = useState("")

  async function submitParameters() {
    const newParameters = {...parameters}

    newParameters.xColumn = xColumn
    newParameters.yColumn = yColumn
    newParameters.zColumn = zColumn
    
    await addCheckbox(newParameters)
  }

  async function addCheckbox(submittedParameters) {
    
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
      await newProps.set(submittedParameters, Points, layerName)

      // Set the new checkbox props and trigger the re-render
      checkboxPropSetters[i](newProps)

      toggleOpen()
  }        

  const columnOptions = []
  for (let i = 0; i < parameters.fields.length; i++) {
    columnOptions.push(
        <option value={parameters.fields[i]} key={parameters.fields[i]}>
            {parameters.fields[i]}
        </option>
    )
  }


  return(
    <div>
      <form>
        <label htmlFor="layerNameInput">Layer Name</label>
        <input type="text" id="layerNameInput" value={layerName} onChange={(e) => setLayerName(e.target.value)}/><br/>
        <label htmlFor="xColumnInput">X Column</label>
        <select id="xColumnInput" value={xColumn} onChange={e => setXColumn(e.target.value)}>
            {columnOptions}  
        </select> <br/>
        <label htmlFor="yColumnInput">Y Column</label>
        <select id="yColumnInput" value={yColumn} onChange={e => setYColumn(e.target.value)}>
            {columnOptions}  
        </select> <br/>
        <label htmlFor="zColumnInput">Z Column</label>
        <select id="zColumnInput" value={zColumn} onChange={e => setZColumn(e.target.value)}>
            {columnOptions}  
        </select> <br/>
      </form>
      <input type="submit" onClick={async () => await submitParameters()}/>
    </div>
  )
}


async function importPoints(fileText, xColumn, yColumn, zColumn) {
    const lines = fileText.split("\n");

    // 5. map through all the lines and split each line by comma.
    const data = lines.map((line) => line.split(","));

    // Push all the columns to the fields property
    const fields = []
    for (let i=0; i<data[0].length; i++) fields.push(data[0][i])

    const parameters = {
        xColumn: xColumn,
        yColumn: yColumn,
        zColumn: zColumn,
        points: data,
        fields: fields
    }

    return parameters
}

function getMinMax(data, nBands, band) {
  let minVal = 9999999
  let maxVal = -9999999
  for (let i = band; i < data.length; i+=nBands) {

    if (data[i] < minVal) {minVal = data[i]}
    if (data[i] > maxVal) {maxVal = data[i]}

  }

  return([minVal, maxVal])
}


export default PointsModal
