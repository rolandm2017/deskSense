// errors.ts
class ImpossibleToGetHereError extends Error {
    constructor(message = "This code path should be impossible to reach.") {
        super(message);
        this.name = "ImpossibleToGetHereError";
    }
}

class ChannelPageOnlyError extends Error {
    constructor(
        message = "This code only runs on a channel's page, which must have an @."
    ) {
        super(message);
        this.name = "ChannelPageOnlyError";
    }
}

class TrackerInitializationError extends Error {
    constructor(
        message = "VisitTracker had no current value when it should have"
    ) {
        super(message);
        this.name = "TrackerInitializationError";
    }
}

class MissingUrlError extends Error {
    constructor(message = "URL not found when it was supposed to be") {
        super(message);
        this.name = "MissingUrlError";
    }
}

class MissingMediaError extends Error {
    constructor(message = "Media not found when it was supposed to be") {
        super(message);
        this.name = "MissingMediaError";
    }
}

export {
    ChannelPageOnlyError,
    ImpossibleToGetHereError,
    MissingMediaError,
    MissingUrlError,
    TrackerInitializationError,
};
