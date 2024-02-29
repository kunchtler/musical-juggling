from __future__ import annotations
import networkx as nx
from collections.abc import Hashable
from typing import TypeVar, Generic, Optional, Collection, TYPE_CHECKING
from collections import deque
from copy import deepcopy
import pyvis
from frozendict import frozendict

# TODO: Rename trans to letter as we have already defined a struct Transition ?
_State = TypeVar("_State", bound=Hashable)
_Trans = TypeVar("_Trans")

# Dirty trick to make both mypy and python happy
# see https://github.com/python/mypy/issues/5264
# fmt:off
if TYPE_CHECKING:
    class _MultiDiGraph(nx.MultiDiGraph[_State]):
        pass
else:
    class _MultiDiGraph(Generic[_State], nx.MultiDiGraph):
        pass
# fmt:on


class Automaton(Generic[_State, _Trans], _MultiDiGraph[_State]):
    """A generic class to describe an automaton.
    Under the hood, the automaton is a networkx DiGraph.
    The transitions are given by the "transition" attribute of edges."""

    def __init__(
        self,
        initial_states: Optional[set[_State]] = None,
        final_states: Optional[set[_State]] = None,
        alphabet: Optional[set[_Trans]] = None,
        graph: Optional[nx.MultiDiGraph[_State]] = None,
    ) -> None:
        super().__init__(graph)
        self.initial_states: set[_State] = (
            set() if initial_states is None else initial_states
        )
        self.final_states: set[_State] = set() if final_states is None else final_states
        self.alphabet: set[_Trans] = set() if alphabet is None else alphabet

    @classmethod
    def to_automaton(cls, aut: Automaton[_State, _Trans]) -> Automaton[_State, _Trans]:
        aut = deepcopy(aut)
        return Automaton(aut.initial_states, aut.final_states, aut.alphabet, aut)

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

    """def flatten(self) -> nx.DiGraph[_State]:
        flatten_graph: nx.DiGraph[_State] = nx.DiGraph()
        for state in self.nodes:
            """

    def is_determined(self) -> bool:
        if len(self.initial_states) != 1:
            return False
        for state in self.nodes:
            already_met_letters: set[_Trans] = set()
            trans: _Trans
            for state1, state2, trans in self.out_edges(state, data="transition"):
                if trans in already_met_letters:
                    return False
                already_met_letters.add(trans)
        return True

    def gather_alphabet(self) -> set[_Trans]:
        alphabet: set[_Trans] = set()
        trans: _Trans
        for _, _, trans in self.edges(data="transition"):
            alphabet.add(trans)
        return alphabet

    # TODO : When there are no final states ?
    def minimize(self) -> Automaton[int, _Trans]:
        if not self.is_determined():
            raise ValueError("Can't minimize nondeterministic automaton")
        # Moore algorithm
        # Graph can be incomplete, as we create a "phantom garbage state" of value -1.
        partition = [self.final_states, set(self.nodes) - self.final_states]
        if len(partition[-1]) == 0:
            # This is possible when all states are final
            partition.pop(1)
        alphabet_list = list(self.alphabet)
        #letter_to_int = {letter: i for i, letter in enumerate(alphabet_list)}
        while True:
            node_to_partition_idx: dict[_State, int] = {}
            for part_idx, part in enumerate(partition):
                for node in part:
                    node_to_partition_idx[node] = part_idx

            new_partition: list[set[_State]] = []
            for part in partition:
                refined_partition: dict[frozendict[_Trans, int], set[_State]] = {}
                for node1 in part:
                    tmp = {letter : -1 for letter in alphabet_list}
                    trans: _Trans
                    for _, node2, trans in self.out_edges(node1, data="transition"):
                        tmp[trans] = node_to_partition_idx[node2]
                    tmp2 = frozendict(tmp)
                    if tmp2 not in refined_partition:
                        refined_partition[tmp2] = set()
                    refined_partition[tmp2].add(node1)
                new_partition.extend(refined_partition.values())

            if partition == new_partition:
                break
            partition = new_partition

        min_automaton: Automaton[int, _Trans] = Automaton()
        min_automaton.add_nodes_from(range(len(partition)))
        min_automaton.alphabet = self.alphabet

        for part_node1, part in enumerate(partition):
            min_automaton.nodes[part_node1]["fused_nodes"] = frozenset(part)
            witness_node1 = part.pop()
            part.add(witness_node1)
            letter: _Trans
            for _, witness_node2, letter in self.out_edges(
                witness_node1, data="transition"
            ):
                part_node2 = node_to_partition_idx[witness_node2]
                if not min_automaton.has_edge(part_node1, part_node2, key=letter):
                    min_automaton.add_edge(
                        part_node1,
                        part_node2,
                        key=letter,
                        transition=letter,
                        label=letter,
                    )

        for part_node, part in enumerate(partition):
            witness_node = part.pop()
            part.add(witness_node)
            if witness_node in self.final_states:
                min_automaton.final_states.add(part_node)
            for node in part:
                if node in self.initial_states:
                    min_automaton.initial_states.add(part_node)
                    break
        return min_automaton

    def determinize(self) -> Automaton[frozenset[_State], _Trans]:
        # Determinzes an automaton. Doesn't make it complete.
        det_automaton: Automaton[frozenset[_State], _Trans] = Automaton()
        to_process: deque[frozenset[_State]] = deque()
        nodes_met = set()
        det_state = frozenset(self.initial_states)
        to_process.append(det_state)
        det_automaton.add_node(det_state, label=str(det_state))
        det_automaton.initial_states.add(det_state)

        while len(to_process) != 0:
            det_state1 = to_process.popleft()
            transitions: dict[_Trans, set[_State]] = {}
            for state1 in det_state1:
                letter: _Trans
                for _, state2, letter in self.out_edges(state1, data="transition"):
                    if letter not in transitions:
                        transitions[letter] = set()
                    transitions[letter].add(state2)
            for letter, det_state2_unfrozen in transitions.items():
                det_state2 = frozenset(det_state2_unfrozen)
                if det_state2 not in nodes_met:
                    nodes_met.add(det_state2)
                    to_process.append(det_state2)
                    det_automaton.add_node(det_state, label=str(det_state))
                det_automaton.add_edge(
                    det_state1, det_state2, key=letter, transition=letter, label=letter
                )

        det_automaton.alphabet = deepcopy(self.alphabet)
        for det_state in det_automaton.nodes:
            if len(self.final_states & det_state) != 0:
                det_automaton.final_states.add(det_state)

        return det_automaton

    def draw_interactive(self, filename, node_name_map = None, show_buttons = False):
        aut = deepcopy(self)

        # Deletes all elements not known to pyvisjs (else crashes)
        # This list of attributes is not extensive
        for _, attr in aut.nodes(data=True):
            for key in list(attr.keys()):
                if key not in ['size', 'value', 'title', 'x', 'y', 'label', 'color']:
                    attr.pop(key, None)
        for _, _, attr in aut.edges(data=True):
            for key in list(attr.keys()):
                if key not in ['value', 'title', 'label', 'color']:
                    attr.pop(key, None)
        
        # Colors the nodes if initial/final/both
        for node in aut.nodes():
            if node in aut.initial_states and node in aut.final_states:
                aut.nodes[node]["color"] = "#b969ff" #purple
            elif node in aut.initial_states:
                aut.nodes[node]["color"] = "#f2e65c" #yellow
            elif node in aut.final_states:
                aut.nodes[node]["color"] = "#fa3939" #red
            else:
                aut.nodes[node]["color"] = "#ff873d" #orange
        
        # Renames the states to be drawable
        if node_name_map is None:
            node_name_map = {state : str(state) for state in self.nodes}
        clean_graph = nx.relabel_nodes(aut, node_name_map)

        nt = pyvis.network.Network(height="900px", width="100%", directed=True)
        nt.from_nx(clean_graph)        
        if show_buttons:
            nt.show_buttons(filter_=['physics', 'nodes', 'edges'])
        with open(filename, "w") as file:
            file.write(nt.generate_html(filename))
        return nt

if __name__ == "__main__":
    aut = Automaton(set([0, 1]), set([2]), set(["a", "b"]))
    #aut.add_edges_from([[0, 2, {"transition" : "a", "label" : "a"}], [1, 2, {"transition" : "b", "label" : "b"}]])