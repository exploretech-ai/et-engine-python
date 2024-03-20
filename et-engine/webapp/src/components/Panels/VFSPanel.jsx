import React, {useState, useEffect} from "react";
import { fetchAuthSession } from '@aws-amplify/auth';

const VFSPanel = () => {
    const [data, setData] = useState(null);

    const fetchData = async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
          console.log(err);
        }

        const response = await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs", {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + session.tokens.idToken.toString()
                }
            }
        );
        const result = await response.json();
        setData(result);
    };



  useEffect(() => {
    fetchData()
  }, [])



    return (
        <div>
            <p>Available Virtual File Systems:</p>
            {data && <p>{data}</p>}
        </div>
    )
}

export default VFSPanel