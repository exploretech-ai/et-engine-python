import React, {useEffect} from "react";
import Directory from "./Directory";

const CodeTab = ({idToken, activeTool}) => {
    
    return (
        <Directory idToken={idToken} resource={activeTool} command={"/code"}/>
    )
}

export default CodeTab