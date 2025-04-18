class ImpossibleToGetHereError extends Error {
    constructor(message = "This code path should be impossible to reach.") {
        super(message)
        this.name = "ImpossibleToGetHereError"
    }
}

class ChannelPageOnlyError extends Error {
    constructor(
        message = "This code only runs on a channel's page, which must have an @."
    ) {
        super(message)
        this.name = "ChannelPageOnlyError"
    }
}
