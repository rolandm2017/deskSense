export class MissingComponentError extends Error {
    constructor(message = "The expected component was missing") {
        super(message);
        this.name = "MissingComponentError";
    }
}
