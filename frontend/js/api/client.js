import { API_URL } from "../config.js";

export async function get(path) {
	const response = await fetch(`${API_URL}${path}`);

	if (!response.ok) {
		throw new Error(
			`API request failed: ${response.status} ${response.statusText}`,
		);
	}

	return response.json();
}

export async function post(path, body) {
	const response = await fetch(`${API_URL}${path}`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(body),
	});

	if (!response.ok) {
		throw new Error(
			`API request failed: ${response.status} ${response.statusText}`,
		);
	}

	return response.json();
}

