import { onWakingChange } from "../api/activity.js";
import { WAKE_MESSAGE_INTERVAL_MS } from "../config.js";

// Shown one after another while the backend is waking up. The last one stays
// until the backend answers.
const WAKING_MESSAGES = [
	"😪 The AI agents have fallen asleep... just a moment while we wake them up.",
	"⏰ Waking up the AI agents... You can still play Human vs. Human in the meantime!",
	"☕ Brewing some coffee to get the agents moving...",
	"🥱 Booting up the AI kernels and initializing agent processes...",
	"🛠️ Configuring agent environments and loading dependencies...",
	"🌐 Establishing connections to the AI network...",
	"🤖 Almost there! Just a few more seconds..."
];

const UNAVAILABLE_MESSAGE =
	"The AI agents can't be reached right now. You can still play Human vs Human.";

let noticeElement = null;
let spinnerElement = null;
let messageElement = null;

let waking = false;
let unavailable = false;
let messageIndex = 0;
let messageTimer = null;

function render() {
	if (waking) {
		spinnerElement.hidden = false;
		messageElement.textContent = WAKING_MESSAGES[messageIndex];
		noticeElement.classList.remove("loading--unavailable");
		noticeElement.hidden = false;
		return;
	}

	if (unavailable) {
		spinnerElement.hidden = true;
		messageElement.textContent = UNAVAILABLE_MESSAGE;
		noticeElement.classList.add("loading--unavailable");
		noticeElement.hidden = false;
		return;
	}

	noticeElement.hidden = true;
}

function stopRotatingMessages() {
	if (messageTimer !== null) {
		clearTimeout(messageTimer);
		messageTimer = null;
	}
}

function showNextMessage() {
	messageTimer = null;

	if (!waking || messageIndex >= WAKING_MESSAGES.length - 1) {
		return;
	}

	messageIndex += 1;
	render();
	messageTimer = setTimeout(showNextMessage, WAKE_MESSAGE_INTERVAL_MS);
}

function setWaking(isWaking) {
	waking = isWaking;
	stopRotatingMessages();

	if (waking) {
		messageIndex = 0;
		messageTimer = setTimeout(showNextMessage, WAKE_MESSAGE_INTERVAL_MS);
	}

	render();
}

// Says that the AI agents could not be reached. Nothing is disabled: the
// notice does not stop anyone playing Human vs Human.
export function setAgentsUnavailable(isUnavailable) {
	unavailable = isUnavailable;
	render();
}

export function initBackendNotice(element) {
	noticeElement = element;
	spinnerElement = element.querySelector(".loading__spinner");
	messageElement = element.querySelector("[data-notice-message]");

	onWakingChange(setWaking);
}
