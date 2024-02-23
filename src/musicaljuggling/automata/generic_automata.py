from __future__ import annotations
import networkx as nx
from collections.abc import Hashable
from typing import TypeVar, Generic, Optional, Collection, TYPE_CHECKING
from collections import deque
from copy import deepcopy

_State = TypeVar("_State", bound=Hashable)
_Trans = TypeVar("_Trans")

# Dirty trick to make both mypy and python happy
# see https://github.com/python/mypy/issues/5264
if TYPE_CHECKING:

    class _DiGraph(nx.DiGraph[_State]):
        pass
else:

    class _DiGraph(Generic[_State], nx.DiGraph):
        pass


class Automaton(Generic[_State, _Trans], _DiGraph[_State]):
    def __init__(self) -> None:
        super().__init__(self)
        self.initial_states: set[_State] = set()
        self.final_states: set[_State] = set()
        self.alphabet: set[_Trans] = set()

    def bfs(self, sources: Collection[_State], reverse: bool = False) -> set[_State]:
        to_process: deque[_State] = deque(sources)
        states_met = set(sources)
        while len(to_process) != 0:
            state1 = to_process.popleft()
            neighbours = (
                self.predecessors(state1) if reverse else self.successors(state1)
            )
            for state2 in neighbours:
                if state2 not in states_met:
                    states_met.add(state2)
                    to_process.append(state2)
        return states_met

    def accessible_states(
        self, sources: Optional[Collection[_State]] = None
    ) -> set[_State]:
        if sources is None:
            sources = self.initial_states
        return self.bfs(sources)

    def coaccessible_states(
        self, sources: Optional[Collection[_State]] = None
    ) -> set[_State]:
        if sources is None:
            sources = self.final_states
        return self.bfs(sources, reverse=True)

    def elagate(self, in_place: bool = False) -> Automaton:
        aut = self if in_place else deepcopy(self)
        nodes_to_remove = set(self.nodes) - (
            self.accessible_states() & self.coaccessible_states()
        )
        aut.remove_nodes_from(nodes_to_remove)
        return aut

    def draw(self, path: str, notebook: bool = False) -> None:
        aut_to_draw = nx.nx_agraph.to_agraph(self)  # type: ignore
        aut_to_draw.layout("dot")
        aut_to_draw.draw(path)
        if notebook:
            from IPython.display import SVG, display

            display(SVG(path))
