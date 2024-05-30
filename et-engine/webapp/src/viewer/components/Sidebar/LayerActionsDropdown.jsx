import React from "react"
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEllipsisH, faTrash, faPencil, faICursor, faArrowsToCircle } from '@fortawesome/free-solid-svg-icons';
import Dropdown from '../../Dropdown';

/**
 * 
 * @param {map} props (named arg) checkbox properties to tie the dropdown menu to (a react state)
 * @param {setState} setProps (named arg) property setter for checkbox properties (a react setState)
 * @param {setState} setOrbit (named arg) property setter for the orbit center
 * @returns a Dropdown menu item tied to the input checkbox
 */
function DropdownMenu({ props, setProps, setFocus }) { 

    // When the delete menu item is clicked, this function clears the checkbox properties and resets it to invisible
    function handleDelete(e) {

        // Copy properties
        console.log(props)
        let newProps = props.clone()
        newProps.reset()

        // Update and re-render with new properties
        setProps(newProps)
    }

    // When the focus item is clicked, this function calculates the bounding box center and sets the orbit controls target to it
    function handleFocus(e) {
        let newProps = props.clone()
        setFocus(newProps)
    }

    // When the rename item is clicked, this function updates the checkbox properties to let it know to reset the label to a text box
    function handleRename(e) {

        // Set the renaming key to true so the label re-renders as a textinput
        let newProps = props.clone()
        newProps.renaming = true

        // Update the checkbox properties and re-render to switch the label to a text input
        setProps(newProps)
    }

    function handleStyle(e){
        let newProps = props.clone()
        newProps.styling = true

        setProps(newProps)
    }
    return (
        <Dropdown>
            <Dropdown.Button>
                <FontAwesomeIcon icon={faEllipsisH} style={{ align: 'center', color: '#000000'}} />
            </Dropdown.Button>
            <Dropdown.Menu>
                <Dropdown.Item onClick={handleStyle}>
                    <span className="dropdownMenuIcon"><FontAwesomeIcon icon={faPencil} /></span>
                    <span>Edit Style</span>
                </Dropdown.Item>
                <Dropdown.Item onClick={handleRename}>
                    <span className="dropdownMenuIcon"><FontAwesomeIcon icon={faICursor} /></span>
                    <span>Rename</span>
                </Dropdown.Item>
                <Dropdown.Item onClick={handleFocus}>
                    <span className="dropdownMenuIcon"><FontAwesomeIcon icon={faArrowsToCircle} /></span>
                    <span>Focus</span>
                </Dropdown.Item>
                <Dropdown.Item onClick={handleDelete}>
                    <span className="dropdownMenuIcon"><FontAwesomeIcon icon={faTrash} /></span>
                    <span>Delete</span>
                </Dropdown.Item>
            </Dropdown.Menu>
        </Dropdown>
      );
}


export default DropdownMenu