import React, { useState } from "react"

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus } from '@fortawesome/free-solid-svg-icons';

import ImportWizard from "../ImportWizards/ImportWizard";
import useToggle from "../../hooks/useToggle";
import Dropdown from "../../Dropdown";

/**
 * Dropdown menu object for loading new objects into the scene
 * @param {Array} checkboxProps the global list of checkbox properties (react States) associated with each element
 * @param {Array} checkboxPropSetters the global list of checkbox property settters (react States)
 * @returns a dropdown menu that lets the user load new objects
 */
function NewObjectMenu({style}) {
    const [modalOpen, toggleModal] = useToggle(false)
    const [modalKey, setModalKey] = useState(null)

    const startWizard = (name) => {
        setModalKey(name)
        toggleModal()
    }

    return(
        <div style={style}>
            {modalOpen && <ImportWizard modalKey={modalKey} toggleOpen={toggleModal}/>}

            <Dropdown>
                <Dropdown.Button>
                    <FontAwesomeIcon icon={faPlus} style={{ align: 'center', color: '#000000'}} />
                    Add New Layer
                </Dropdown.Button>
                <Dropdown.Menu className="dropdown-content">
                    <Dropdown.Item onClick={() => startWizard("Surface")}>Surface</Dropdown.Item>
                    <Dropdown.Item onClick={() => startWizard("Points")}>Points</Dropdown.Item>
                    <Dropdown.Item onClick={() => startWizard("Lines")}>Lines</Dropdown.Item>
                    <Dropdown.Item onClick={() => startWizard("Ensemble")}>Ensemble</Dropdown.Item>
                    <Dropdown.Item onClick={() => startWizard("Drillhole")}>Drillhole</Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
        </div>
    )
}


export default NewObjectMenu