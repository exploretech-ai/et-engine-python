import React, {useState} from "react";
import Dropdown from '../../../Dropdown';
import { TerrainColormap, SeismicColormap } from '../../../layers/geometries/Colormaps';


/**
 * Creates a slider that modifies the layer opacity
 * @param {Integer} i integer specifying which unique value to connect the opacity to
 * @param {state} checkboxProps checkbox props to associate the slider with
 * @param {setState} checkboxPropSetter setter for the checkbox props
 * @returns a slider that controls opacity connected to the checkbox
 */
function LithOpacitySlider({i, checkboxProps, checkboxPropSetter}) {

    // Initialize the opacity state
    const [opacity, setOpacity] = useState(checkboxProps.object.material[i].opacity)

    /**
     * Sets the opacity and modifies the checkbox properties with the new opacity
     * @param {event} e 
     */
    function updateOpacity(e) {

        // Fetch the opacity from the slider
        const newOpacity = e.target.value

        // Set the opacity in the material
        const newProps = checkboxProps.clone()
        newProps.object.material[i].opacity = newOpacity

        // If the opacity is very low then make the mesh completely invisible
        if (newOpacity < 0.02) {
            newProps.object.scene.children[i].visible = false
        } else {
            newProps.object.scene.children[i].visible = true
        }
        
        // Update the React states
        checkboxPropSetter(newProps)
        setOpacity(newOpacity)
    }


    return (
        <span>
            Opacity {i} 
            <input type="range" min="0" max="1" step=".01" value={opacity} onChange={(e) => updateOpacity(e)} style={{marginLeft: "10px"}}/>
        </span>
    )
}

/**
 * 
 * @param {CheckBoxProps} checkboxProps (named arg) react state checkbox properties associated with the styler
 * @param {setState} checkboxPropSetter (named arg) react state setter for checkbox properties
 * @returns a styling JSX element that the user can interact with the modify the layer style
 */
function MultiVolumeStyler({checkboxProps, checkboxPropSetter}) {

    const [colorMap, setColorMap] = useState(null)              // For the colormap used to set colors
    
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

        // Use the new colormap to update the mesh colors and then update the rendering
        newProps.object.setColors(colorMapOptions[cmap])
        checkboxPropSetter(newProps)
    }

    // Add sliders for each unique value
    const sliders = []
    for (let i = 0; i < checkboxProps.object.geometry.length; i++) {
        sliders.push(
            <LithOpacitySlider i={i} checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} key={i} />
        )
    }

    // Each style option is contained within a <span> block
    return(
        <span>
            Colormap
            <Dropdown style={{marginLeft: "10px"}}>
                <Dropdown.Toggle variant="success" className="styler-color-field">
                    {colorMap ? colorMap:"Select From List"}
                </Dropdown.Toggle>

                <Dropdown.Menu>
                    <Dropdown.Item onClick={() => updateColorMap('Seismic')} key={"seismic"}>
                        Seismic
                    </Dropdown.Item>
                    <Dropdown.Item onClick={() => updateColorMap('Terrain')} key={"terrain"}>
                        Terrain
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
            {sliders}
        </span>
    )
}


export default MultiVolumeStyler