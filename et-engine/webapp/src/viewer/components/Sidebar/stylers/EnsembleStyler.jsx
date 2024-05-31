import React, {useState} from "react";
import Dropdown from '../../../Dropdown'
import { TerrainColormap, SeismicColormap } from '../../../layers/geometries/Colormaps';

const colorMapOptions = {
    'Seismic': SeismicColormap,
    'Terrain': TerrainColormap
}

const colorMapOptionsReverse = {
    SeismicColormap: 'Seismic',
    TerrainColormap: 'Terrain'
}

/**
 * Creates a slider that modifies the layer opacity
 * @param {Integer} i integer specifying which unique value to connect the opacity to
 * @param {state} checkboxProps checkbox props to associate the slider with
 * @param {setState} checkboxPropSetter setter for the checkbox props
 * @returns a slider that controls opacity connected to the checkbox
 */
function LithOpacitySlider({i, checkboxProps, checkboxPropSetter, style}) {

    // Initialize the opacity state
    const [opacity, setOpacity] = useState(checkboxProps.object.material[i].opacity)

    /**
     * Sets the opacity and modifies the checkbox properties with the new opacity
     * @param {event} e event associated with a change in the opacity scroller
     */
    function updateOpacity(e) {

        // Fetch the opacity from the slider
        const newOpacity = e.target.value

        // Set the opacity in the material
        const newProps = checkboxProps.clone()
        newProps.object.setOpacity(newProps.object.uniqueValues[i], newOpacity)

        // Update the React states
        setOpacity(newOpacity)
        checkboxPropSetter(newProps)
    }

    return (
        <span style={{display: 'flex'}}>
            Opacity {i} 
            <input type="range" min="0" max="1" step=".01" value={opacity} onChange={(e) => updateOpacity(e)} style={style}/>
        </span>
    )
}

/**
 * Creates a number input box that lets you scroll through the realizations
 * @param {state} checkboxProps checkbox props to associate the slider with
 * @param {setState} checkboxPropSetter setter for the checkbox props
 * @returns a Number input box attached to the checkbox
 */
function RealizationScroller({checkboxProps, checkboxPropSetter}) {

    // Initialize React states
    const [realization, setRealization] = useState(0)
    const [label, setLabel] = useState(checkboxProps.object.parameters.fileNames[0])

    /**
     * Updates the realization set to visible
     * @param {event} e event associated with a change in the number input box
     */
    function updateRealization(e) {

        const realizationNumber = e.target.value

        // Make sure the number is between 0-numReals
        if (realizationNumber >= 0 && realizationNumber < checkboxProps.object.numRealizations) {

            // Update the checkbox properties with new realization visible
            const newProps = checkboxProps.clone()
            newProps.object.setVisible(realizationNumber)

            // Update React states
            checkboxPropSetter(newProps)
            setRealization(realizationNumber)
            setLabel(checkboxProps.object.parameters.fileNames[realizationNumber])
        }
    }
    
    return (
        <div>
        <span style={{display: 'flex'}}>
            Realization  
            <input type="number" value={realization} onChange={(e) => updateRealization(e)} style={{marginLeft: "10px"}}/>
        </span>
        {label}
        </div>
    )
}

/**
 * 
 * @param {CheckBoxProps} checkboxProps (named arg) react state checkbox properties associated with the styler
 * @param {setState} checkboxPropSetter (named arg) react state setter for checkbox properties
 * @returns a styling JSX element that the user can interact with the modify the layer style
 */
function EnsembleStyler({checkboxProps, checkboxPropSetter}) {

    const [colorMap, setColorMap] = useState(colorMapOptionsReverse[checkboxProps.object.style.colorMap.name])              // For the colormap used to set colors
    
    /**
     * Updates colors based on a colormap change only
     * @param {string} cmap string identifier for the colormap, either 'Seismic' or 'Terrain'
     */
    function updateColorMap(cmap) {

        // Update the displayed color field
        setColorMap(cmap)

        // Update the colormap property on the layer object
        let newProps = checkboxProps.clone()

        // Use the new colormap to update the mesh colors and then update the rendering
        newProps.object.setColors(colorMapOptions[cmap])
        checkboxPropSetter(newProps)
    }

    // Add sliders for each unique value
    const sliders = []
    for (let i = 0; i < checkboxProps.object.uniqueValues.length; i++) {
        sliders.push(
            <LithOpacitySlider i={i} checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} key={i} style={{marginLeft: "10px"}}/>
        )
    }

    // Each style option is contained within a <span> block
    return(
        <div>
            <span>
                Colormap
                <Dropdown style={{marginLeft: "10px"}}>
                    <Dropdown.Button>
                        {colorMap ? colorMap:"Select From List"}
                    </Dropdown.Button>

                    <Dropdown.Menu>
                        <Dropdown.Item onClick={() => updateColorMap('Seismic')} key={"seismic"}>
                            Seismic
                        </Dropdown.Item>
                        <Dropdown.Item onClick={() => updateColorMap('Terrain')} key={"terrain"}>
                            Terrain
                        </Dropdown.Item>
                    </Dropdown.Menu>
                </Dropdown>
            </span>
            {sliders}
            <RealizationScroller checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/>
        </div>
    )
}


export default EnsembleStyler