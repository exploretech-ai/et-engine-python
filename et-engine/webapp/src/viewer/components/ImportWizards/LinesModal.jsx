import React, {useRef, useContext, useState} from "react"
import { CBContext } from "../../../pages/Viewer";
import './modal.css'
import Lines from "../../layers/Lines";

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
      const file = document.getElementById("newLines").files[0]
      
      // NOTE: THIS IS SUPPOSED TO STOP THIS FUNCTION IF THE USER CANCELS THE FILE UPLOAD BUT DOESNT WORK
      if (file === undefined) {
          return
      }

      const parameters = await importLines(await file.text())
      setParameters(parameters)
      setLayerName(file.name)
      setPage(2)

  }

  return(
    <div>
      <p>Upload a csv with your line data. The CSV should have the following columns (x-coord, y-coord, z-coord, lineID)</p>
      <input 
          type='file' 
          name={"newLines"}
          id={"newLines"}
          ref={inputRef} 
          onChange={async () => await createNew()} 
          onClick={(e) => e.stopPropagation()} // without the stopPropagation the box does not click
          accept={".csv"}
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
  const [lineColumn, setLineColumn] = useState("")


  async function submitParameters() {
    const newParameters = {...parameters}
    newParameters.xColumn = xColumn
    newParameters.yColumn = yColumn
    newParameters.zColumn = zColumn
    newParameters.lineColumn = lineColumn

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
      await newProps.set(submittedParameters, Lines, submittedName)

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
        <label htmlFor="lineColumnInput">Line ID Column</label>
        <select id="lineColumnInput" value={lineColumn} onChange={e => setLineColumn(e.target.value)}>
            {columnOptions}  
        </select> <br/>

      </form>
      <input type="submit" onClick={async () => await submitParameters(layerName)}/>
    </div>
  )
}



async function importLines(fileText) {

    // 4. split the text by newline
    const lines = fileText.split("\n");

    // 5. map through all the lines and split each line by comma.
    const data = lines.map((line) => line.split(","));

    // Push all the columns to the fields property
    const fields = []
    for (let i=0; i<data[0].length; i++) fields.push(data[0][i])

    const parameters = {
        xColumn: "x_27",
        yColumn: "y_27",
        zColumn: "altitude",
        lineColumn: "Line",
        points: data,
        fields: fields
    }

    return parameters

}

export default LinesModal
