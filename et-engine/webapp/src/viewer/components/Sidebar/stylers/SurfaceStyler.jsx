import React, {useRef, useState} from "react";
import { TerrainColormap, SeismicColormap } from '../../../layers/geometries/Colormaps';
import Dropdown from "../../../Dropdown";
import { fromBlob } from "geotiff";


const colorMapOptions = {
    'Seismic': SeismicColormap,
    'Terrain': TerrainColormap
}

const colorMapOptionsReverse = {
    SeismicColormap: 'Seismic',
    TerrainColormap: 'Terrain'
}

function OpacitySlider({checkboxProps, checkboxPropSetter}) {
    const [opacity, setOpacity] = useState(checkboxProps.object.style.opacity)

    function updateOpacity(e) {
        setOpacity(e.target.value)
        const newProps = checkboxProps.clone()
        newProps.object.setOpacity(e.target.value)
        checkboxPropSetter(newProps)
    }

    return (
        <span>
            Opacity
            <input type="range" min="0" max="1" step=".01" value={opacity} onChange={(e) => updateOpacity(e)} style={{marginLeft: "10px"}}/>
        </span>
    )
}


function ColorMapSelector({checkboxProps, checkboxPropSetter, colorMap, setColorMap}) {

    /**
     * Updates colors based on a colormap change only
     * @param {string} cmap string identifier for the colormap, either 'Seismic' or 'Terrain'
     */
    function updateColorMap(cmap) {
        setColorMap(cmap)
        let newProps = checkboxProps.clone()
        newProps.object.geometry.setColors(colorMapOptions[cmap])
        checkboxPropSetter(newProps)
    }

    return(
        <span style={{display: 'flex'}}>
            Colormap
            <Dropdown style={{marginLeft: "10px"}}>
                <Dropdown.Button>
                    {colorMap ? colorMap:"Select From List"}
                </Dropdown.Button>
                <Dropdown.Menu>
                    <Dropdown.Item onClick={() => {updateColorMap('Seismic')}}>
                        Seismic
                    </Dropdown.Item>
                    <Dropdown.Item onClick={() => {updateColorMap('Terrain')}}>
                        Terrain
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
        </span>
    )
}


function BandSelector({checkboxProps, checkboxPropSetter, colorMap}) {
    const [colorBand, setColorBand] = useState(1)

    const bandOptions = []
    for (let i = 0; i < checkboxProps.object.parameters.nBands; i++) {
        const [minVal, maxVal] = checkboxProps.object.geometry.getMinMax(i + 1)

        bandOptions.push(
            <option value={i+1} key={i+1}>
                {(i+1).toString() + " (min " + minVal.toString() + ", max " + maxVal.toString() + ")"}
            </option>
        )
    }

    function updateColors(e) {
        const newColorBand = e.target.value
        setColorBand(newColorBand)

        const newCheckbox = checkboxProps.clone()
        newCheckbox.object.geometry.parameters.colorBand = Number(newColorBand)
        newCheckbox.object.geometry.setColors(colorMapOptions[colorMap])
        checkboxPropSetter(newCheckbox)
    }

    return(
        <span>
            Color Band:
            <select id="elevBand" value={colorBand} onChange={e => updateColors(e)} style={{marginLeft: "10px"}}>
                {bandOptions}  
            </select>
        </span>
    )
}

const AddBand = ({checkboxProps, checkboxPropSetter}) => {

    const inputFile = useRef(null) 


    const handleClick = () => {
        inputFile.current.click();
    }


    const addBandFromFile = async (e) => {

        console.log('Adding new band...')

        // Fetch the new data
        const file = document.getElementById("file").files[0]
        const tiff = await fromBlob(file)
        const image = await tiff.getImage()
        const rasterData = await image.readRasters({interleave: true});
        const pixelData = Array.from(rasterData)

        // Update the checkbox properties with the new data
        const newCheckbox = checkboxProps.clone()
        newCheckbox.object.geometry.parameters.nBands = newCheckbox.object.geometry.parameters.nBands + 1
        newCheckbox.object.parameters.nBands = newCheckbox.object.geometry.parameters.nBands

        const numPixels = newCheckbox.object.geometry.parameters.width * newCheckbox.object.geometry.parameters.height 
        const newData = []

        for (let i = 0; i < numPixels; i += 1) {
            for (let j = 0; j < newCheckbox.object.parameters.nBands - 1; j += 1) {
                newData.push(newCheckbox.object.parameters.data[i * (newCheckbox.object.parameters.nBands - 1) + j])
            }
            newData.push(pixelData[i])
        }
        newCheckbox.object.geometry.parameters.data = newData
        newCheckbox.object.parameters.data = newData
        checkboxPropSetter(newCheckbox)
    }

    return(
        <span>
            <Dropdown>
                <Dropdown.Button>
                    Add Band
                </Dropdown.Button>
                <Dropdown.Menu>
                    <Dropdown.Item onClick={handleClick}>
                        from file
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
            <input type='file' id='file' ref={inputFile} onChange={addBandFromFile} style={{display: 'none'}}/>
        </span>
    )
}

/**
 * 
 * @param {CheckBoxProps} checkboxProps (named arg) react state checkbox properties associated with the styler
 * @param {setState} checkboxPropSetter (named arg) react state setter for checkbox properties
 * @returns a styling JSX element that the user can interact with the modify the layer style
 */
function SurfaceStyler({checkboxProps, checkboxPropSetter}) {

    const [colorMap, setColorMap] = useState(colorMapOptionsReverse[checkboxProps.object.style.colorMap.name])                  // For the colormap used to set colors

    // Each style option is contained within a <span> block
    return(
        <div>
            <ColorMapSelector checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} colorMap={colorMap} setColorMap={setColorMap}/>
            <BandSelector checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} colorMap={colorMap}/>
            <OpacitySlider checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} />
            <AddBand checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/>
        </div>
    )
}


export default SurfaceStyler