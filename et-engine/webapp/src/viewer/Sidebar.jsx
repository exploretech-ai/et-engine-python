import React, { useContext } from "react";
import NewLayerDropdown from "./components/Sidebar/NewLayerDropdown";
import { CBContext } from "../pages/Viewer";

/**
 * Sidebar consisting of an object loader and a layer modifier
 * @returns JSX that renders the sidebar elements
 */
function Sidebar() {

  const [checkboxes, checkboxProps, checkboxPropSetters] = useContext(CBContext)

  // Fucntion to render only checkboxes that are noted as visible
  const renderCheckboxes = () => {
    const checkboxList = []
    for (let i=0; i<checkboxProps.length; i++){ 
      if (checkboxProps[i].visible) {
        checkboxList.push(checkboxes[i])
      }
    }
    return checkboxList
  }

  async function saveProject() {

    let fileContents = []
    for (let i = 0; i < checkboxProps.length; i++) {
      fileContents.push(await checkboxProps[i].toFile())
    }
    console.log(fileContents)

    const element = document.createElement("a");
    const file = new Blob([fileContents.join('\n---\n')], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = "my-project.project";
    document.body.appendChild(element); // Required for this to work in FireFox
    element.click();

  }

  // Returns only rendered checkboxes + properties and setters
  return ([
    <div>
      <NewLayerDropdown />
      <fieldset>
        <legend>Select Layers:</legend>
          {renderCheckboxes()}
      </fieldset>
      <button onClick={saveProject}>Save Project</button>
    </div>
  ]);
}


export default Sidebar