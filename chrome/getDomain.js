import { reportTabSwitch } from "./api"

chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    if (tabs[0]) {
        let url = new URL(tabs[0].url)
        let domain = url.hostname
        console.log(domain) // e.g., "www.example.com"

        reportTabSwitch(domain)
    }
})
