import {
	IDLE_BACKEND_THRESHOLD_MS,
	REFRESH_COOLDOWN_MS,
} from "../config.js";
import { msSinceLastContact, onContact } from "./activity.js";

// Calls onIdle() when the browser has not heard from the backend for
// IDLE_BACKEND_THRESHOLD_MS while the page is visible.
//
// Nothing runs while the page is hidden. The watcher reacts to the page
// becoming visible, to the window regaining focus, to the browser coming
// back online, and to a single timer that is only armed while the page is
// visible. Returns a function that stops watching.
export function watchBackendIdle(onIdle) {
	let timer = null;
	let refreshing = false;

	// The page has only just loaded, so count that as an attempt. This stops
	// an event right after loading from repeating the initial request.
	let lastAttemptAt = Date.now();

	function isVisible() {
		return document.visibilityState === "visible";
	}

	function stopTimer() {
		if (timer !== null) {
			clearTimeout(timer);
			timer = null;
		}
	}

	function startTimer(delay) {
		stopTimer();
		timer = setTimeout(check, delay);
	}

	async function check() {
		stopTimer();

		if (!isVisible() || refreshing) {
			return;
		}

		const idleFor = msSinceLastContact();

		if (idleFor < IDLE_BACKEND_THRESHOLD_MS) {
			startTimer(IDLE_BACKEND_THRESHOLD_MS - idleFor);
			return;
		}

		if (Date.now() - lastAttemptAt < REFRESH_COOLDOWN_MS) {
			return;
		}

		refreshing = true;
		lastAttemptAt = Date.now();

		try {
			await onIdle();
		} catch {
			// The caller reports failures. Nothing is scheduled, so the
			// next event tries again once the cooldown has passed.
		} finally {
			refreshing = false;
		}
	}

	function handleVisibilityChange() {
		if (isVisible()) {
			check();
		} else {
			stopTimer();
		}
	}

	// Every answer from the backend restarts the countdown.
	const stopListeningForContact = onContact(() => {
		if (isVisible()) {
			startTimer(IDLE_BACKEND_THRESHOLD_MS);
		}
	});

	document.addEventListener("visibilitychange", handleVisibilityChange);
	window.addEventListener("focus", check);
	window.addEventListener("online", check);
	window.addEventListener("pageshow", check);

	return function stop() {
		stopTimer();
		stopListeningForContact();

		document.removeEventListener("visibilitychange", handleVisibilityChange);
		window.removeEventListener("focus", check);
		window.removeEventListener("online", check);
		window.removeEventListener("pageshow", check);
	};
}
