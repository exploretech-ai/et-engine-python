import React, { useContext } from "react";
import { CBContext } from "../../../pages/Viewer";

/**
 * Creates a Three.js model
 * @param {Array} checkboxProps Array with the properties of each checkbox
 * @returns primitive with loaded scene
 */
function Model({ setFocus }) {
  const [, checkboxProps, ] = useContext(CBContext)

  // Initialize the scene
  const sceneList = []

  // Loop through each checkbox and load only those that are visible and checked
  let numActive = 0
  for (let i=0; i<checkboxProps.length; i++) {
    if (checkboxProps[i].visible) {

      // Increase the number of active/visible checkboxes
      numActive++

      // Only load checked items
      if (checkboxProps[i].checked) {
        sceneList.push(<primitive key={'scene' + i} object={checkboxProps[i].object.scene} />)
      }
    }
  }

  // Focus on the first thing loaded if there's only one object
  if (numActive == 1) {
    setFocus(checkboxProps[0])
  }

  // Return empty plot if there's nothing loaded, otherwise return the scene
  if (numActive == 0) {

    return undefined

  } else {

    return (
      <group>
          {sceneList}
      </group>
    )

  }
}


export default Model