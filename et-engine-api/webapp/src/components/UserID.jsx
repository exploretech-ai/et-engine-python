import React, {useState} from "react"



function Algorithm({id, name}) {
  // 

  return (
      <div style={{border: "1px solid black"}}>
          <p>ID: {id}</p>
          <span>
              <p>Name: {name}</p>
              <button>Provision</button>
              <button>Build</button>
              <button>Execute</button>
              <button>Destroy</button>
          </span>
      </div>
  )
}


function UserID({userID, setUserID}) {


    
  const [itemData, setItemData] = useState([])

    const handleInputChange = (event) => {
        setUserID(event.target.value);
      };

    const handleApiRequest = async () => {
        try {
          const response = await fetch(`https://gsgj2z3zpj.execute-api.us-east-2.amazonaws.com/prod/users/${userID}/workflows`);
          const data = await response.json();
          console.log(data)
          setItemData(data)
          // setItemData([0, 1])

        } catch (error) {
          console.error('Error fetching data:', error);
        }
      };
    

    return (
        <div>
            <label>Enter User ID:</label>
            <input
                type="text"
                id="userID"
                value={userID}
                onChange={handleInputChange}
            />
            <button onClick={handleApiRequest}>Submit</button>
            {itemData.map((item, index) => (<Algorithm id={item[0]} name={item[2]} key={item}/>))}
        </div>
    )
}

export default UserID