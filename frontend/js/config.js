const isLocal = ["localhost", "127.0.0.1"].includes(
	window.location.hostname
);

export const API_URL = isLocal
	? "/api"
	: "https://via-ludus-api.onrender.com/api";

export const AI_MOVE_DELAY = 250;

// The hosted backend runs on a free tier that puts it to sleep when nobody
// is using it. A local backend never sleeps, so the "waking up" notice is
// only used when the backend is hosted.
export const BACKEND_MAY_SLEEP = !isLocal;

// A request that has waited longer than this (in milliseconds) shows the
// "waking up the AI agents" notice, if the backend plausibly went to sleep.
export const SLOW_REQUEST_THRESHOLD_MS = 5 * 1000;

// If the browser has not heard from the backend for this long (in
// milliseconds), it refreshes the agent menus, which also wakes the backend.
// Keep this shorter than the time the host waits before putting the backend
// to sleep (15 minutes on Render's free tier).
export const IDLE_BACKEND_THRESHOLD_MS = 10 * 60 * 1000;

// If the browser has not heard from the backend for this long (in
// milliseconds), the backend is assumed to be asleep. Only then does a slow
// request say that the agents are waking up; otherwise a slow request is
// just a slow agent.
export const BACKEND_SLEEP_AFTER_MS = 15 * 60 * 1000;

// The minimum time (in milliseconds) between automatic attempts to refresh
// the agent menus, so that a backend that is down is not asked repeatedly.
export const REFRESH_COOLDOWN_MS = 30 * 1000;

// How often (in milliseconds) the "waking up" notice moves on to its next
// message.
export const WAKE_MESSAGE_INTERVAL_MS = 8 * 1000;
