/* Pairs with options.html */

// Initialize variables
let ignoredDomains = []

// Load existing domains when options page opens
document.addEventListener("DOMContentLoaded", loadDomains)

// Setup event listeners
document.getElementById("uploadButton").addEventListener("click", uploadDomains)
document
    .getElementById("addDomainButton")
    .addEventListener("click", addSingleDomain)
document
    .getElementById("saveManualEdit")
    .addEventListener("click", saveManualEdit)
document
    .getElementById("clearAllButton")
    .addEventListener("click", clearAllDomains)
document.getElementById("exportButton").addEventListener("click", exportDomains)

// Load domains from storage
function loadDomains() {
    chrome.storage.local.get("ignoredDomains", function (data) {
        ignoredDomains = data.ignoredDomains || []
        displayDomains()
        updateManualEditArea()
    })
}

// Display domains in the list
function displayDomains() {
    const list = document.getElementById("domainsList")
    list.innerHTML = ""

    if (ignoredDomains.length === 0) {
        list.innerHTML = "<p>No domains in the ignore list.</p>"
        return
    }

    ignoredDomains.forEach((domain, index) => {
        const item = document.createElement("div")
        item.className = "domain-item"

        const domainText = document.createElement("span")
        domainText.textContent = domain

        const deleteButton = document.createElement("button")
        deleteButton.textContent = "Delete"
        deleteButton.className = "delete-btn"
        deleteButton.addEventListener("click", () => removeDomain(index))

        item.appendChild(domainText)
        item.appendChild(deleteButton)
        list.appendChild(item)
    })
}

// Update the manual edit textarea
function updateManualEditArea() {
    document.getElementById("manualEdit").value = ignoredDomains.join("\n")
}

// Upload domains from file
function uploadDomains() {
    const fileInput = document.getElementById("domainsFile")
    const file = fileInput.files[0]

    if (file) {
        const reader = new FileReader()
        reader.onload = function (e) {
            const fileContent = e.target.result
            const newDomains = fileContent
                .split("\n")
                .map((line) => line.trim())
                .filter((line) => line !== "" && !line.startsWith("#"))

            // Add new domains without duplicates
            newDomains.forEach((domain) => {
                if (!ignoredDomains.includes(domain)) {
                    ignoredDomains.push(domain)
                }
            })

            saveDomains()
        }
        reader.readAsText(file)
    }
}

// Add a single domain
function addSingleDomain() {
    const input = document.getElementById("newDomain")
    const domain = input.value.trim()

    if (domain && !ignoredDomains.includes(domain)) {
        ignoredDomains.push(domain)
        saveDomains()
        input.value = ""
    }
}

// Save manual edits
function saveManualEdit() {
    const text = document.getElementById("manualEdit").value
    ignoredDomains = text
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line !== "" && !line.startsWith("#"))

    saveDomains()
}

// Remove a domain by index
function removeDomain(index) {
    ignoredDomains.splice(index, 1)
    saveDomains()
}

// Clear all domains
function clearAllDomains() {
    if (confirm("Are you sure you want to clear all domains?")) {
        ignoredDomains = []
        saveDomains()
    }
}

// Export domains to a file
function exportDomains() {
    const content = ignoredDomains.join("\n")
    const blob = new Blob([content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)

    const a = document.createElement("a")
    a.href = url
    a.download = "ignored_domains.txt"
    a.click()

    setTimeout(() => URL.revokeObjectURL(url), 100)
}

// Save domains to Chrome storage
function saveDomains() {
    if (chrome.storage && chrome.storage.local) {
        chrome.storage.local.set(
            { ignoredDomains: ignoredDomains },
            function () {
                displayDomains()
                updateManualEditArea()
            }
        )
    } else {
        console.error("chrome.storage.local is not available")
    }
}
