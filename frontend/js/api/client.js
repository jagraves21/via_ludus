import { API_URL } from "../config.js";
import { isBackendResponse, trackRequest } from "./activity.js";

async function request(path, options) {
	const finish = trackRequest();
	let reachedBackend = false;

	try {
		const response = await fetch(`${API_URL}${path}`, options);

		reachedBackend = isBackendResponse(response);

		if (!response.ok) {
			throw new Error(
				`API request failed: ${response.status} ${response.statusText}`,
			);
		}

		return await response.json();
	} finally {
		finish({ reachedBackend });
	}
}

export async function get(path) {
	return request(path);
}

export async function post(path, body) {
	return request(path, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(body),
	});
}
