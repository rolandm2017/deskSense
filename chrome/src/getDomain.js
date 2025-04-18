// // getDomain.js
// import { reportTabSwitch } from "./api"

// // "Find the currently active tab in the current window, and when you find it, run this function with the tab information"
// chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
//     if (tabs[0]) {
//         console.log("in getDomain.js")
//         let url = new URL(tabs[0].url)
//         let domain = url.hostname
//         console.log(domain, "Title:", tabs[0].title)
//         reportTabSwitch(domain, tabs[0].title)
//     }
// })
