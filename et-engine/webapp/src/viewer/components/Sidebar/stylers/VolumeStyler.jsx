import React, {useState} from "react";
import Dropdown from '../../../Dropdown';
import { TerrainColormap, SeismicColormap } from '../../../objects/geometries/Colormaps';

/**
 * 
 * @param {CheckBoxProps} checkboxProps (named arg) react state checkbox properties associated with the styler
 * @param {setState} checkboxPropSetter (named arg) react state setter for checkbox properties
 * @returns a styling JSX element that the user can interact with the modify the layer style
 */
function VolumeStyler({checkboxProps, checkboxPropSetter}) {

    const [colorMap, setColorMap] = useState(null)              // For the colormap used to set colors
    const [opacity, setOpacity] = useState(1.0)

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

    function updateOpacity(e) {
        setOpacity(e.target.value)
        const newProps = checkboxProps.clone()
        newProps.object.material.opacity = e.target.value

        checkboxPropSetter(newProps)
    }

    

    // Each style option is contained within a <span> block
    return(
        <div>
            <span style={{display: 'flex'}}>
                Colormap
                <Dropdown>
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
            </span>
            <span style={{display: 'flex'}}>
                Opacity
                <input type="range" min="0" max="1" step=".01" value={opacity} onChange={(e) => updateOpacity(e)}/>
            </span>
        </div>
    )
}

export default VolumeStyler