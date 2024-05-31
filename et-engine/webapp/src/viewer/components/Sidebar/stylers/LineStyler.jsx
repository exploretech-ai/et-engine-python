import React, {useState} from "react";
import { TerrainColormap, SeismicColormap } from '../../../layers/geometries/Colormaps';
import Dropdown from "../../../Dropdown"

const colorMapOptions = {
    'Seismic': SeismicColormap,
    'Terrain': TerrainColormap
}

const colorMapOptionsReverse = {
    SeismicColormap: 'Seismic',
    TerrainColormap: 'Terrain'
}


function ColorMapSelector({checkboxProps, checkboxPropSetter, colorField}) {

    const [colorMap, setColorMap] = useState(colorMapOptionsReverse[checkboxProps.object.style.colorMap.name])                  // For the colormap used to set colors

    /**
     * Updates colors based on a colormap change only
     * @param {string} cmap string identifier for the colormap, either 'Seismic' or 'Terrain'
     */
    function updateColorMap(cmap) {

        // These are the pre-defined colormap options
        const colorMapOptions = {
            'Seismic': SeismicColormap,
            'Terrain': TerrainColormap
        }

        // Update the displayed color field
        setColorMap(cmap)

        // Update the colormap property on the layer object
        let newProps = checkboxProps.clone()
        newProps.object.style.colorMap = colorMapOptions[cmap]

        // Use the new colormap to update the mesh colors and then update the rendering
        newProps.object.setColors(colorField)
        checkboxPropSetter(newProps)
    }
   
    // Each style option is contained within a <span> block
    return(
        <span>
            Colormap
            <Dropdown style={{marginLeft: "10px"}}>
                <Dropdown.Button>
                    {colorMap ? colorMap:"Select From List"}
                </Dropdown.Button>
                <Dropdown.Menu>
                    <Dropdown.Item onClick={() => updateColorMap('Seismic')}>
                        Seismic
                    </Dropdown.Item>
                    <Dropdown.Item onClick={() => updateColorMap('Terrain')}>
                        Terrain
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
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

function TransformSelector({checkboxProps, checkboxPropSetter, colorField}) {
    const [transform, setTransform] = useState(checkboxProps.object.style.transform ? checkboxProps.object.style.transform.name: null)            // For the mathematical transform used in the color scale
    
    /**
     * Sets the mathematical transform used to update the mesh colors
     * @param {string} transformName string identifier for the mathematical transform used to set colors, either 'None' or 'Log'
     */
    function updateTransform(transformName) {

        // These are the pre-defined transform options
        const transformOptions = {
            'None': null,
            'Log': Math.log10
        }

        // Update the dropdown box label
        setTransform(transformName)

        // Update the transform in the layer object
        let newProps = checkboxProps.clone()
        newProps.object.style.transform = transformOptions[transformName]

        // Update the colors with the new transform and re-render
        newProps.object.setColors(colorField)
        checkboxPropSetter(newProps)
    }

    return (
        <span>
            Transform
            <Dropdown style={{marginLeft: "10px"}}>
                <Dropdown.Button>
                    {transform ? transform:"Select From List"}
                </Dropdown.Button>
                <Dropdown.Menu>
                    <Dropdown.Item onClick={() => updateTransform('None')}>
                        None
                    </Dropdown.Item>
                    <Dropdown.Item onClick={() => updateTransform('Log')}>
                        Log
                    </Dropdown.Item>
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
function LineStyler({checkboxProps, checkboxPropSetter}) {

    const [colorField, setColorField] = useState(checkboxProps.object.style.colorValue)          // For the color variable to display on the lines
    const [colorMap, setColorMap] = useState(checkboxProps.object.style.colorMap.name)              // For the colormap used to set colors
    const [width, setWidth] = useState(checkboxProps.object.style.width)                      // For the rendering line width

    /**
     * Updates colors based on a colormap change only
     * @param {string} cmap string identifier for the colormap, either 'Seismic' or 'Terrain'
     */
    function updateColorMap(cmap) {

        // These are the pre-defined colormap options
        const colorMapOptions = {
            'Seismic': SeismicColormap,
            'Terrain': TerrainColormap
        }

        // Update the displayed color field
        setColorMap(cmap)

        // Update the colormap property on the layer object
        let newProps = checkboxProps.clone()
        newProps.object.style.colorMap = colorMapOptions[cmap]

        // Use the new colormap to update the mesh colors and then update the rendering
        newProps.object.setColors(colorField)
        checkboxPropSetter(newProps)
    }

    /**
     * Updates the mesh width along the lines
     * @param {Number} newWidth line mesh width in new render
     */
    function updateWidth(newWidth) {

        // Update the width property
        let newProps = checkboxProps.clone()
        newProps.object.geometry.width = newWidth

        // Update the mesh and re-render with new props
        newProps.object.geometry.updateGeometry()
        checkboxPropSetter(newProps)
    }

    // Each style option is contained within a <span> block
    return(
        <div>
            <ColorFieldSelector colorField={colorField} setColorField={setColorField} checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/>
            <ColorMapSelector colorField={colorField} checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/>
            <TransformSelector colorField={colorField} checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/>
            {/* <span style={{display: 'flex'}}>
                Transparency
            </span> */}
            <span style={{display: 'flex'}}>
                Width
                <input type="number" value={width} onChange={(e) => setWidth(e.target.value)} style={{marginLeft: "10px"}}/>
                <button type="submit" onClick={() => updateWidth(width)}>Submit</button>

            </span>
        </div>
    )
}


export default LineStyler