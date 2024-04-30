import React, {useEffect} from "react";
import Directory from "./Directory";

const CodeTab = ({idToken, activeTool}) => {


    return (
        <Directory idToken={idToken} activeTool={activeTool} />
    )
}

export default CodeTab