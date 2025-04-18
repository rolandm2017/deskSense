// api.js

const DESKSENSE_BACKEND_URL = "http://localhost:8000"

const chromeTabUrl = "/api/chrome/tab"
const youTubeUrl = "/api/chrome/youtube"
const ignoredDomainUrl = "/api/chrome/ignored"

export function reportYouTube(tabTitle, channel) {
    const payload = {
        url: "www.youtube.com",
        tabTitle,
        channel,
        startTime: new Date(),
    }
    sendPayload(youTubeUrl, payload)
}

export function reportIgnoredUrl() {
    const payload = {
        url: "ignored", // Must match the pydantic definition
        tabTitle: "ignored",
        startTime: new Date(),
    }
    console.log("Sending payload:", payload)

    sendPayload(ignoredDomainUrl, payload)
}

export function reportTabSwitch(domain, tabTitle) {
    const payload = {
        url: domain, // Must match the pydantic definition
        tabTitle: tabTitle,
        startTime: new Date(),
    }
    // console.log("Sending payload:", payload)

    sendPayload(chromeTabUrl, payload)
}

function sendPayload(targetUrl, payload) {
    fetch(DESKSENSE_BACKEND_URL + targetUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    })
        .then((response) => {
            // Note there is no JSON in a 204

            // console.log("Status Code:", response.status) // Log the status code
            if (response.status === 204) {
                console.log("")
                // console.log("200 good to go")
            } else {
                throw new Error(`Request failed with status ${response.status}`)
            }
        })
        .catch((error) => console.error("Error:", error))
}
