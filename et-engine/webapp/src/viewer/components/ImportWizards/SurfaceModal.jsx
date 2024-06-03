import React, {useRef, useContext, useState} from "react"
import { CBContext } from "../../../pages/Viewer";
import { fromBlob } from "geotiff";
import './modal.css'
import Surface from "../../layers/Surface";

/*
This dialog box operates a wizard with 2 pages. The first page lets you upload a file. The second page lets you adjust the import parameters.
*/
function SurfaceModal({toggleOpen}) {

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
      const file = document.getElementById("newSurface").files[0]
      
      // NOTE: THIS IS SUPPOSED TO STOP THIS FUNCTION IF THE USER CANCELS THE FILE UPLOAD BUT DOESNT WORK
      if (file === undefined) {
          return
      }

      const parameters = await importSurface(file)
      setParameters(parameters)
      setLayerName(file.name)
      setPage(2)
  }

  return(
    <div>
      <p>Upload a single-band GeoTiff containing elevation data</p>
      <input 
          type='file' 
          name={"newSurface"}
          id={"newSurface"}
          ref={inputRef} 
          onChange={async () => await createNew()} 
          onClick={(e) => e.stopPropagation()} // without the stopPropagation the box does not click
          accept={[".tif", ".tiff", ".geotiff", ".DEM"]}
          multiple={true}
      />
    </div>
  )
}
function Page2({parameters, layerName, setLayerName, toggleOpen}) {
  const [noDataInput, setNoData] = useState(parameters.noData)
  const [elevationBand, setElevationBand] = useState(1)
  const [, checkboxProps, checkboxPropSetters] = useContext(CBContext)

  async function submitParameters() {
    const newParameters = {...parameters}
    newParameters.noData = Number(noDataInput)
    newParameters.elevationBand = Number(elevationBand)
    newParameters.colorBand = Number(elevationBand)
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
      await newProps.set(submittedParameters, Surface, layerName)

      // Set the new checkbox props and trigger the re-render
      checkboxPropSetters[i](newProps)

      toggleOpen()
  }        

  const bandOptions = []
  for (let i = 0; i < parameters.nBands; i++) {
    const [minVal, maxVal] = getMinMax(parameters.data, parameters.nBands, i)

    bandOptions.push(
        <option value={i+1} key={i+1}>
            {(i+1).toString() + " (min " + minVal.toString() + ", max " + maxVal.toString() + ")"}
        </option>
    )
  }

  return(
    <div>
      <form>
        <label htmlFor="layerNameInput">Layer Name</label>
        <input type="text" id="layerNameInput" value={layerName} onChange={(e) => setLayerName(e.target.value)}/><br/>
        <label htmlFor="NoDataInput">No-Data Value</label>
        <input type="number" id="NoDataInput" value={noDataInput} onChange={(e) => setNoData(e.target.value)}/><br/>
        <label htmlFor="elevBand">Elevation Band</label>
        <select id="elevBand" value={elevationBand} onChange={e => setElevationBand(e.target.value)}>
            {bandOptions}  
        </select> <br/>
      </form>
      <input type="submit" onClick={async () => await submitParameters()}/>
    </div>
  )
}


async function importSurface(file) {
  // console.log(file)
  const tiff = await fromBlob(file)
  // const tiff = await fromArrayBuffer(file)
  const image = await tiff.getImage()
  const data = await image.readRasters({interleave: true});
  const origin = image.getOrigin()
  const resolution = image.getResolution()

  const {width, height} = data

  const parameters = {
      origin: origin,
      resolution: resolution,
      data: Array.from(data),
      noData:-32767,
      nBands: image.fileDirectory.SamplesPerPixel,
      elevationBand: 1,
      colorBand: 1,
      width: width,
      height: height
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


export default SurfaceModal
