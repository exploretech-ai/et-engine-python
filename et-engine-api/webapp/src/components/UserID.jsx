import React, {useState} from "react"

function Details({itemDetails}) {

    return (
        <div>
            <p>{itemDetails === null ? "hello" : itemDetails}</p>
        </div>
    )
}

function UserID() {


    const [userId, setUserId] = useState('');
    const [itemDetails, setItemDetails] = useState(null);

    const handleInputChange = (event) => {
        setUserId(event.target.value);
      };

    const handleApiRequest = async () => {
        try {
            console.log(userId)
            // setItemDetails(userId)
          const response = await fetch(`https://gsgj2z3zpj.execute-api.us-east-2.amazonaws.com/prod/users/${userId}`);
          const data = await response.json();
        console.log(data)
          setItemDetails(JSON.stringify(data))
        } catch (error) {
          console.error('Error fetching data:', error);
        //   setApiResult(null);
        }
      };
    

    return (
        <div>
            <label>User ID:</label>
            <input
                type="text"
                id="userId"
                value={userId}
                onChange={handleInputChange}
            />
            <button onClick={handleApiRequest}>Submit</button>
            <Details itemDetails={itemDetails}/>
        </div>
    )
}

export default UserID