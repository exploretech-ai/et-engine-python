import React, {useState} from "react"
import Page from "./Page"
import "./Viewer.css"

import Viewer from "../viewer/Viewer"
import Projects from "../viewer/Projects"
import Checkbox from '../viewer/components/Sidebar/Checkbox';
import '../viewer/components/ImportWizards/modal.css'

export const CBContext = React.createContext()

const ViewerPage = () => {

    const [viewer, setViewer] = useState(false)
    const [focus, setFocus] = useState(null)

    // Number of checkboxes to initialize
    const maxCheckboxes = 20
    
    // Initialize arrays to hold checkboxes and their properties
    const checkboxes = new Array(maxCheckboxes)
    const checkboxProps = new Array(maxCheckboxes)
    const checkboxPropSetters = new Array(maxCheckboxes)

    // Populate checkboxes and properties
    for (let i=0; i<maxCheckboxes; i++){
        const [cb, p, sp] = Checkbox(i, setFocus)
        checkboxes[i] = cb
        checkboxProps[i] = p
        checkboxPropSetters[i] = sp
    }

    return(
        <Page name="Viewer" style={{paddingLeft: 0, paddingRight: 0}}>
            <CBContext.Provider value={[checkboxes, checkboxProps, checkboxPropSetters]}>
                {viewer ? 
                    <Viewer focus={focus} setFocus={setFocus}/>
                :
                    <Projects setViewer={setViewer} setFocus={setFocus}/>
                }
            </CBContext.Provider>  
        </Page>
    )
}

export default ViewerPage