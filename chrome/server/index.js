const express = require("express")
const bodyParser = require("body-parser")

// Initialize express app
const app = express()

// Middleware to parse JSON bodies
app.use(bodyParser.json())

app.get("/", (req, res) => {
    res.status(200).json({ message: "Server is online" })
})

// POST route handler
app.post("/", (req, res) => {
    // Check if domain exists in request body
    if (!req.body.domain) {
        return res.status(400).json({
            error: "Missing domain field in request body",
        })
    }

    const { domain } = req.body

    // Log the received domain
    console.log(`Received domain: ${domain}`)

    // Send success response
    res.status(200).json({
        message: "Domain received successfully",
        domain: domain,
    })
})

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack)
    res.status(500).json({
        error: "Something went wrong!",
    })
})

// Start server
const PORT = 8080
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`)
})
