import React, { useState } from "react";
import LayerActionsDropdown from "./LayerActionsDropdown";
import ElementRename from "./ElementRename";
import Styler from "./Styler";

import LayerProps from "../../io/Layer";

import "./Checkbox.css"

  /**
   * Creates a special checkbox item with associated properties
   * @param {any} initLabel The id and initial label of the checkbox
   * @returns [checkbox element, checkbox properties, checkbox property setter]
   */
  function Checkbox(initLabel, setFocus) {
  
    // Initialize the properties for the checkbox
    const [props, setProps] = useState(new LayerProps(initLabel))
    
    // change checked property when checkbox state is changed
    function handleChange() {
      let newProps = props.clone()
      newProps.checked = !props.checked
      setProps(newProps)
    }
  
    // This controls whether the render the renaming element
    let renameElement = props.label
    if (props.renaming) {
    
        renameElement = [
          <ElementRename 
              key={'rename' + initLabel} 
              initLabel={'renameInput' + initLabel} 
              checkboxProps={props} 
              checkboxPropsSetter={setProps}
          />, 
          <p key={'instructions' + initLabel}>Press Enter to Save</p>
        ]
    }

    // If you're styling, then push a styler
    let styleElement = null
    if (props.styling) {
      styleElement = <Styler checkboxProps={props} checkboxPropSetter={setProps}/>
    }
  
    // Render a checkbox (with modifiers) with an attached dropdown menu. Also return the state and setstate for the checkbox properties.
    return ([
      <div key={'element' + initLabel} className="plotElement"> 
        <div key={'elementName' + initLabel} className="plotElementName">
          <label key={'label' + initLabel}> 
            <input 
              key={'checkbox' + initLabel}
              type="checkbox" 
              checked={props.checked} 
              onChange={() => handleChange()} 
              style={{marginRight: 5}}
              />
          {renameElement}
          </label>
          <LayerActionsDropdown 
            props={props} 
            setProps={setProps} 
            setFocus={setFocus}
          />
        </div>
        {styleElement}
      </div>,
      props,
      setProps
    ])
  }

  export default Checkbox