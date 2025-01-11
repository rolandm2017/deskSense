export function reportTabSwitch(domain) {
    fetch("http://localhost:8080", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            domain: domain,
        }),
    })
        .then((response) => response.json())
        .catch((error) => console.error("Error:", error))
}
