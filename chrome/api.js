// api.js

const DESKSENSE_BACKEND_URL = "http://localhost:8000"

const chromeTabUrl = "/chrome/tab"

export function reportTabSwitch(domain, title) {
    const payload = {
        url: domain,  // Must match the pydantic definition
        tabTitle: title,
        startTime: new Date()
    }
    console.log("Sending payload:", payload)
    
    fetch(DESKSENSE_BACKEND_URL + chromeTabUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    })
        .then((response) => {
            // Note there is no JSON, it's a 204!
            
            console.log("Status Code:", response.status); // Log the status code
            if (response.status === 204) {
                console.log("200 good to go")
            } else {
                throw new Error(`Request failed with status ${response.status}`);
            }
        })
        .catch((error) => console.error("Error:", error))
}