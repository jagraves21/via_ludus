from . import board
from .board import (
	Cell,
	PlayerColor,
	Board,
	SearchBoard,
	UnionFindBoard,
)

from . import player
from .player import (
	Player,
	DeterministicMoveSelectionMixin,
	ScoringPlayer,
	DeterministicScoringMixin,
	MoveSelector,
	BestSelector,
	MaxSelector,
	MinSelector,
	RandomBestSelector,
	RandomMaxSelector,
	RandomMinSelector,
	SoftmaxSelector,
	SoftminSelector,
	MaxSelectorMixin,
	MinSelectorMixin,
	RandomMaxSelectorMixin,
	RandomMinSelectorMixin,
	SoftmaxSelectorMixin,
	SoftminSelectorMixin,
)

from . import validation
from . import tournament

from . import ai
from .ai import (
	AI_AGENTS,
	VIA_LUDUS_AGENTS,
)

from . import utils


__all__ = [
	"Cell",
	"PlayerColor",
	"Board",
	"SearchBoard",
	"UnionFindBoard",

	"Player",
	"DeterministicMoveSelectionMixin",
	"ScoringPlayer",
	"DeterministicScoringMixin",
	"MoveSelector",
	"BestSelector",
	"MaxSelector",
	"MinSelector",
	"RandomBestSelector",
	"RandomMaxSelector",
	"RandomMinSelector",
	"SoftmaxSelector",
	"SoftminSelector",
	"MaxSelectorMixin",
	"MinSelectorMixin",
	"RandomMaxSelectorMixin",
	"RandomMinSelectorMixin",
	"SoftmaxSelectorMixin",
	"SoftminSelectorMixin",

	"AI_AGENTS",
	"VIA_LUDUS_AGENTS",
]


_GRAPH_REGISTRIES = (
	"GRAPH_AGENTS",
	"DISTANCE_AGENTS",
	"PATH_AGENTS",
	"VERTEX_CUT_AGENTS",
	"VERTEX_CENTRALITY_AGENTS",
	"EDGE_CENTRALITY_AGENTS",
)

for name in _GRAPH_REGISTRIES:
	if hasattr(ai, name):
		globals()[name] = getattr(ai, name)
		__all__.append(name)

