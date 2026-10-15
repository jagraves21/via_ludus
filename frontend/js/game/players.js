import { BLUE, RED } from "./state.js";

export function getPlayerName(color) {
	if (color === RED) {
		return "Red";
	}

	if (color === BLUE) {
		return "Blue";
	}

	return "";
}

