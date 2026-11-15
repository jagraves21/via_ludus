import {
	BACKEND_MAY_SLEEP,
	BACKEND_SLEEP_AFTER_MS,
	SLOW_REQUEST_THRESHOLD_MS,
} from "../config.js";

// While the hosted backend is starting up, these come from the host's
// gateway rather than from the backend, so they do not prove it is awake.
const GATEWAY_ERROR_STATUSES = new Set([502, 503, 504]);

let lastContactAt = null;
let wakingRequestCount = 0;

const wakingListeners = new Set();
const contactListeners = new Set();

export function msSinceLastContact() {
	if (lastContactAt === null) {
		return Infinity;
	}

	return Date.now() - lastContactAt;
}

export function isBackendLikelyAsleep() {
	return (
		BACKEND_MAY_SLEEP &&
		msSinceLastContact() >= BACKEND_SLEEP_AFTER_MS
	);
}

export function isBackendResponse(response) {
	return !GATEWAY_ERROR_STATUSES.has(response.status);
}

// Calls listener(true) when a request has been waiting long enough that the
// backend is probably waking up, and listener(false) when no such request
// is left. Returns a function that removes the listener.
export function onWakingChange(listener) {
	wakingListeners.add(listener);

	return () => wakingListeners.delete(listener);
}

// Calls listener() every time the backend answers a request.
export function onContact(listener) {
	contactListeners.add(listener);

	return () => contactListeners.delete(listener);
}

function changeWakingRequestCount(change) {
	const wasWaking = wakingRequestCount > 0;

	wakingRequestCount += change;

	const isWaking = wakingRequestCount > 0;

	if (wasWaking !== isWaking) {
		for (const listener of wakingListeners) {
			listener(isWaking);
		}
	}
}

// Call when a request starts, and call the function it returns when the
// request ends.
export function trackRequest() {
	// Decided when the request starts, so that a request made while the
	// backend was asleep is still recognised after another request has
	// finished.
	const likelyAsleep = isBackendLikelyAsleep();
	let waking = false;

	const timer = setTimeout(
		() => {
			if (!likelyAsleep) {
				return;
			}

			waking = true;
			changeWakingRequestCount(1);
		},
		SLOW_REQUEST_THRESHOLD_MS,
	);

	return function finish({ reachedBackend }) {
		clearTimeout(timer);

		if (reachedBackend) {
			lastContactAt = Date.now();

			for (const listener of contactListeners) {
				listener();
			}
		}

		if (waking) {
			waking = false;
			changeWakingRequestCount(-1);
		}
	};
}
