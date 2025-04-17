describe("a variety of user inputs work as intended", () => {
    test("user can type just the domain", () => {
        const theIgnoreList = [
            "reddit.com",
            "tiktok.com",
            "x.com",
            "google.com",
        ]
        const toBeCensored = [
            "https://www.reddit.com",
            "https://www.youtube.com",
            "https://www.tiktok.com",
            "https://www.x.com",
            "https://mail.google.com",
            "https://docs.google.com",
        ]
    })
    test("user can type the full domain", () => {
        const theIgnoreList = [
            "https://www.reddit.com",
            "https://www.tiktok.com",
            "https://www.x.com",
            "https://www.google.com",
        ]
        const toBeCensored = [
            "https://www.reddit.com",
            "https://www.youtube.com",
            "https://www.tiktok.com",
            "https://www.x.com",
            "https://mail.google.com",
            "https://docs.google.com",
        ]
    })
})
