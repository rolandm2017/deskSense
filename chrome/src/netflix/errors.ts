export class MissingComponentError extends Error {
    constructor(
        component: string,
        message = "The expected component was missing: "
    ) {
        super(message + component);
        this.name = "MissingComponentError";
    }
}
