const isLocal = ["localhost", "127.0.0.1"].includes(
	window.location.hostname
);

export const API_URL = isLocal
	? "/api"
	: "https://via-ludus-api.onrender.com/api";

export const AI_MOVE_DELAY = 250;

