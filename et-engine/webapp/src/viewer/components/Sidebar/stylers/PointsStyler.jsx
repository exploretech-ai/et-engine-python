import React, {useRef, useState} from "react";
import { TerrainColormap, SeismicColormap } from '../../../layers/geometries/Colormaps';
import Dropdown from "../../../Dropdown";


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


function ColorMapSelector({checkboxProps, checkboxPropSetter, colorField}) {

    const [colorMap, setColorMap] = useState(colorMapOptionsReverse[checkboxProps.object.style.colorMap.name])
    /**
     * Updates colors based on a colormap change only
     * @param {string} cmap string identifier for the colormap, either 'Seismic' or 'Terrain'
     */
    function updateColorMap(cmap) {
        setColorMap(cmap)
        let newProps = checkboxProps.clone()
        newProps.object.style.colorMap = colorMapOptions[cmap]
        newProps.object.setColors(colorField)
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


const RadiusSelector = ({checkboxProps, checkboxPropSetter}) => {

    const [radius, setRadius] = useState(checkboxProps.object.style.radius)                      // For the rendering line width

    /**
     * Updates the mesh width along the lines
     * @param {Number} newRadius sphere radius in new render
     */
    function updateRadius(newRadius) {

        // Update the width property
        let newProps = checkboxProps.clone()
        newProps.object.geometry.radius = newRadius

        // Update the mesh and re-render with new props
        newProps.object.geometry.updateGeometry()
        checkboxPropSetter(newProps)
    }

    return (
        <span style={{display: 'flex'}}>
            Radius
            <input type="number" value={radius} onChange={(e) => setRadius(e.target.value)} style={{marginLeft: "10px"}}/>
            <button type="submit" onClick={() => updateRadius(radius)}>Submit</button>
        </span>
    )
}

function ColorFieldSelector({checkboxProps, checkboxPropSetter, colorField, setColorField}) {

    /**
     * Sets the color variable and then updates the color in the 3D plot accordingly
     * @param {string} f the variable that is mapped to a color
     */
    function updateColor(f) {

        // Update the displayed color field
        setColorField(f)

        // Assign new colors to the layer object by updating the checkbox properties
        let newProps = checkboxProps.clone()
        newProps.object.setColors(f)
        newProps.object.style.colorValue = f
        checkboxPropSetter(newProps)
    }

    // This for-loop sets the list of fields available in the dropdown menu. Start by initializing an empty array of fields.
    const fields = []

    // Loop through each field in the object.fields property
    for (let i=0; i<checkboxProps.object.parameters.fields.length; i++) {

        const f = checkboxProps.object.parameters.fields[i]

        // Push the field string to a dropdown menu item and trigger the updateColor function on selection
        fields.push(
            <Dropdown.Item onClick={() => updateColor(f)} key={f}>
                {f}
            </Dropdown.Item>
            )
    }

    return (
        <span>
            Color Field
            <Dropdown style={{marginLeft: "10px"}}>
                <Dropdown.Button>
                    {colorField ? colorField:"Select From List"}
                </Dropdown.Button>
                <Dropdown.Menu>
                    {fields}
                </Dropdown.Menu>
            </Dropdown>
        </span>
    )
}


/**
 * 
 * @param {CheckBoxProps} checkboxProps (named arg) react state checkbox properties associated with the styler
 * @param {setState} checkboxPropSetter (named arg) react state setter for checkbox properties
 * @returns a styling JSX element that the user can interact with the modify the layer style
 */
function PointsStyler({checkboxProps, checkboxPropSetter}) {

    const [colorField, setColorField] = useState(checkboxProps.object.style.colorValue)          // For the color variable to display on the lines

    // Each style option is contained within a <span> block
    return(
        <div>
            <ColorMapSelector checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} colorField={colorField}/>
            <ColorFieldSelector colorField={colorField} setColorField={setColorField} checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/>
            <RadiusSelector checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/>
            <OpacitySlider checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} />
        </div>
    )
}


export default PointsStyler