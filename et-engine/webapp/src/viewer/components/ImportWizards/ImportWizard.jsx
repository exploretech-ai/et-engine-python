import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import './modal.css'

import SurfaceModal from './SurfaceModal'
import LinesModal from './LinesModal'
import EnsembleModal from './EnsembleModal'
import DrillholeModal from './DrillholeModal'

// Creates a portal outside the DOM hierarchy
function Portal({ children }) {
  const modalRoot = document.getElementById('modal-root') // A div with id=modal-root in the index.html
  
  const initElement = document.createElement('div')
  initElement.className = "modal"
  const [element] = useState(initElement) // Create a div element which will be mounted within modal-root

  // useEffect bible: https://overreacted.io/a-complete-guide-to-useeffect/
  useEffect(() => {
    modalRoot.appendChild(element)

    // cleanup method to remove the appended child
    return function cleanup() {
      modalRoot.removeChild(element)
    }
  }, [modalRoot, element])

  return createPortal(children, element)
}

// A modal component which will be used by other components / pages
function ImportWizard({ modalKey, isOpen, toggleOpen }) {

    function getModal(key) {
        switch(key) {
            case "Surface":
                return <SurfaceModal toggleOpen={toggleOpen}/>
            case "Lines":
                return <LinesModal toggleOpen={toggleOpen}/>
            case "Volume":
                return null
            case "Ensemble":
                return <EnsembleModal toggleOpen={toggleOpen}/>
            case "Drillhole":
                return <DrillholeModal toggleOpen={toggleOpen}/>
            default:
                console.log(`Object key ${key} not recognized`)
                return null
        }
    }

  return (
    isOpen && 
    <Portal> 
        <button className="closeButton" onClick={toggleOpen}>X</button>
        {getModal(modalKey)} 
    </Portal>
  )
}


export default ImportWizard
