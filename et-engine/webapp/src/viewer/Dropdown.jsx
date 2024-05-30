import React, { useState } from "react"
import "./Dropdown.css"

const getChildByDisplayName = (children, displayName) => 
    React.Children.map(children, (child) => 
        child.type.displayName === displayName ? child : null 
    )


/**
 * This is the master dropdown box
 */
const Dropdown = ({children, style, ...other}) => {
    const button = getChildByDisplayName(children, "Button")
    const menu = getChildByDisplayName(children, "Menu")

    // const [isOpen, toggleOpen] = useToggle(false)
    const [isOpen, setOpen] = useState(false)
    const [hovered, setHovered] = useState(true)

    return(
        <div className="dropdown" 
          style={{...style}} 
          {...other} 
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => {setHovered(false); setOpen(false)}}
        >
            <div onClick={() => {setOpen(true)}}>
                {button}
            </div>

            <div onClick={() => setOpen(false)}>
            {isOpen & hovered ? menu : null}
            </div>
        </div>
    )
}


/**
 * This button controls when the dropdown box is initiated
 * @param {} param0 
 * @returns 
 */
const Button = ({children, style, ...other}) => {
    
    return(
        <button style={{...style}} {...other}>
            {children}
        </button>
    )
}
Button.displayName = "Button"
Dropdown.Button = Button


/**
 * This holds all the dropdown selections
 * @param {*} param0 
 * @returns 
 */
const Menu = ({children, style, ...other}) => {

    return(
        <div className="dropdown-content" style={{...style}} {...other}>
            {children}
        </div>
    )
}
Menu.displayName = "Menu"
Dropdown.Menu = Menu


/**
 * This is an individual dropdown box item
 * @param {*} param0 
 * @returns 
 */
const Item = ({children, style, ...other}) => {

    return (
        <a style={{...style}} {...other}>
            {children}
        </a>
    )
}
Item.displayName = "Item"
Dropdown.Item = Item


export default Dropdown