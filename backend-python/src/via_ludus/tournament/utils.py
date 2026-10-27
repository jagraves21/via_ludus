from ..player import validate_player

def validate_starting_color(starting_color):
	starting_color = (
		PlayerColor.RED
		if starting_color is None
		else starting_color
	)
	validate_player(starting_color)
	return starting_color

