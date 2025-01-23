// getDomain.js
import { reportTabSwitch } from "./api"

chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    if (tabs[0]) {
        let url = new URL(tabs[0].url)
        let domain = url.hostname
        console.log(domain, "Title:", tabs[0].title)
        reportTabSwitch(domain, tabs[0].title)
    }
})