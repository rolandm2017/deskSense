const baseRoute = import.meta.env.VITE_API_URL + "/api"

const keyboardEventsRoute = baseRoute + "/keyboard"
const mouseEventsRoute = baseRoute + "/mouse"
const programsRoute = baseRoute + "/programs"
const chromeRoute = baseRoute + "/chrome"

interface KeyboardEvent {
    date: Date
    time: Date // fixme - should these be separate?
}

interface MouseEvent {
    startTime: Date
    endTime: Date
    span: number // in ms
}

interface ProgramReport {
    title: string
    duration: number // in minutes
}

interface ChromeReport {
    title: string
    duration: number
}

function getKeyboardEvents() {
    // todo
}

function getMouseEvents() {
    //todo
}

function getProgramUsage() {
    // todo
}

function getChromeTabsTimes() {
    // todo
}
