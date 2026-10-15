import { get } from "./client.js";

export async function getAgents() {
	const response = await get("/agents");

	return response.agents;
}

