import React from "react"

function Algorithm({id, name}) {
    // 

    return (
        <div style={{border: "1px solid black"}}>
            <p>ID: {id}</p>
            <span>
                <p>Name: {name}</p>
                <button>Execute</button>
                <button>Provision</button>
                <button>Build</button>
                <button>Destroy</button>
            </span>
        </div>
    )
}

function AlgorithmsList() {


    async function fetchAvailableAlgorithms(userID) {
        // GET /algorithms?user={userID}
        const response = await fetch(`https://xmnogdgtx4.execute-api.us-east-2.amazonaws.com/prod/users/${userID}/algorithms`);
    }

    return (
        <div>
            <Algorithm id={0} name={"Hello World"}/>
            <Algorithm id={1} name={"Hello World"}/>
        </div>
    )
}

export default AlgorithmsList