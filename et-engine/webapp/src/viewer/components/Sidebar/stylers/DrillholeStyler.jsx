import React, {useState} from "react";
import Dropdown from '../../../Dropdown';
import { TerrainColormap, SeismicColormap } from '../../../layers/geometries/Colormaps';

// These are the pre-defined colormap options
const colorMapOptions = {
    'Seismic': SeismicColormap,
    'Terrain': TerrainColormap
}


/**
 * 
 * @param {CheckBoxProps} checkboxProps (named arg) react state checkbox properties associated with the styler
 * @param {setState} checkboxPropSetter (named arg) react state setter for checkbox properties
 * @returns a styling JSX element that the user can interact with the modify the layer style
 */
function DrillholeStyler({checkboxProps, checkboxPropSetter}) {

    const [colorMap, setColorMap] = useState('Seismic')              // For the colormap used to set colors
    const [realization, setRealization] = useState(0)


    /**
     * Updates the realization set to visible
     * @param {event} e event associated with a change in the number input box
     */
    function updateRealization(e) {

        const realizationNumber = e.target.value

        // Make sure the number is between 0-numReals
        if (realizationNumber >= 0 && realizationNumber < checkboxProps.object.parameters.numObservations) {

            // Update the checkbox properties with new realization visible
            const newProps = checkboxProps.clone()
            newProps.object.currentObservation = realizationNumber
            newProps.object.setColors(colorMapOptions[colorMap])

            // Update React states
            checkboxPropSetter(newProps)
            setRealization(realizationNumber)
        }
    }

    /**
     * Updates colors based on a colormap change only
     * @param {string} cmap string identifier for the colormap, either 'Seismic' or 'Terrain'
     */
    function updateColorMap(cmap) {
        setColorMap(cmap)
        let newProps = checkboxProps.clone()
        newProps.object.setColors(colorMapOptions[cmap])
        checkboxPropSetter(newProps)
    }

    // Each style option is contained within a <span> block
    return(
        <div>
            <span style={{display: 'flex'}}>
                Colormap
                <Dropdown>
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
            <span style={{display: 'flex'}}>
            Property  
            <input type="number" value={realization} onChange={(e) => updateRealization(e)}/>
        </span>
            {/* <TubeRadiusSetter checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/> */}
            {/* <CollarRadiusSetter checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter}/> */}
        </div>
    )
}

// function TubeRadiusSetter({checkboxProps, checkboxPropSetter}) {

//     const [radius, setRadius] = useState(1)

//     function updateTubeRadius(e) {
//         const radius = e.target.value

//         if (radius >= 1) {
//             const newProps = checkboxProps.clone()
//             newProps.object.radius.tube = radius
//             newProps.object.setTube()
    
//             // Update the React states
//             setRadius(radius)
//             checkboxPropSetter(newProps)
//         }
//     }

//     return (
//         <span style={{display: 'flex'}}>
//             Drillhole Radius
//             <input type="number" value={radius} onChange={(e) => updateTubeRadius(e)}/>
//         </span>
//     )
// }

// function CollarRadiusSetter({checkboxProps, checkboxPropSetter}) {

//     const [radius, setRadius] = useState(1)

//     function updateCollarRadius(e) {
//         const radius = e.target.value

//         if (radius >= 1) {
//             const newProps = checkboxProps.clone()
//             newProps.object.radius.sphere = radius
//             newProps.object.setSphere()
    
//             // Update the React states
//             setRadius(radius)
//             checkboxPropSetter(newProps)
//         }
//     }

//     return (
//         <span style={{display: 'flex'}}>
//             Collar Radius  
//             <input type="number" value={radius} onChange={(e) => updateCollarRadius(e)}/>
//         </span>
//     )
// }

export default DrillholeStyler