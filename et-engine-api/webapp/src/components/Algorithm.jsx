import React, {useState} from "react"

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

function AlgorithmsList({userID, setUserID}) {

    const [itemData, setItemData] = useState([])


    async function fetchAvailableAlgorithms() {
        // GET /algorithms?user={userID}
        const userID = "0"
        setItemData([0, 1])
        // const response = await fetch(`https://gsgj2z3zpj.execute-api.us-east-2.amazonaws.com/prod/users/${userID}/algorithms`);
        // const data = await response.json();
        // console.log(data)
    }


    // const items = [0, 1]

    return (
        <div>
            <button onClick={fetchAvailableAlgorithms}>Get Algorithms</button>
            {itemData.map((item, index) => (<Algorithm id={item} name="hello" key={item}/>))}
        </div>
    )
}

export default AlgorithmsList