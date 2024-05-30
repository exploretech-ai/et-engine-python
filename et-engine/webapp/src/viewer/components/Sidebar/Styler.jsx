import React from "react";
import LineStyler from "./stylers/LineStyler";
import SurfaceStyler from "./stylers/SurfaceStyler";
import MultiVolumeStyler from "./stylers/MultiVolumeStyler";
import EnsembleStyler from "./stylers/EnsembleStyler";
import DrillholeStyler from "./stylers/DrillholeStyler";
import "./Styler.css"

/**
 * High-level styler object that conditionally returns the proper styler based on the object type
 * @param {CheckBoxProps} checkboxProps (named arg) react state checkbox properties associated with the styler
 * @param {setState} checkboxPropSetter (named arg) react state setter for checkbox properties
 * @returns a styling JSX element that the user can interact with the modify the layer style
 */
function Styler({checkboxProps, checkboxPropSetter}) {

    // Get the object type so we can conditionally render
    const layerType = checkboxProps.object.type
    
    // Use if-statements to select the proper styler element
    let styler = null

    switch (layerType) {
        case "Lines": 
            styler = <LineStyler checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} />
            break
        case "Surface":
            styler = <SurfaceStyler checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} />
            break
        case "Volume":
            styler = <MultiVolumeStyler checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} />
            break
        case "Ensemble": 
            styler = <EnsembleStyler checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} />
            break
        case "Drillhole": 
            styler = <DrillholeStyler checkboxProps={checkboxProps} checkboxPropSetter={checkboxPropSetter} />
            break
    }

    // When the close button is clicked, this will remove the styler by setting the 'styling' attribute to false
    function closeStyler() {
        let newProps = checkboxProps.clone()
        newProps.styling = false
        checkboxPropSetter(newProps)
    }

    // Just the styler and a close button wrapped into a container
    return(
        <div className="styler-container">
            <button className="styler-close-button" onClick={closeStyler}>X</button>
            {styler}
        </div>
    )

}

export default Styler