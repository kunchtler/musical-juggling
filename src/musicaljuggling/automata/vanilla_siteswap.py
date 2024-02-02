import networkx as nx
from itertools import combinations
from typing import Type, Iterable, NamedTuple


def stringify[T](iter: Iterable[T]) -> str:
    return "".join(str(elem) for elem in iter)


class State(tuple):
    def shift_state(self) -> Type["State"]:
        return State(self[(i + 1) % len(self)] for i in range(len(self)))

    def enumerate_transitions(self) -> list[Type["Transition"]]:
        if self[0] == 0:
            return [Transition(self, 0, self.shift_state())]
        shifted_state = list(self.shift_state())
        shifted_state[-1] = 0
        transitions = []
        for i, elem in enumerate(shifted_state):
            if elem == 0:
                new_state = list(shifted_state)
                new_state[i] = 1
                transitions.append(Transition(self, i + 1, State(new_state)))
        return transitions


class Transition(NamedTuple):
    begin_state: State
    throw: int
    end_state: State


class VanillaSiteswapAutomaton:
    def __init__(self, nb_balls: int, max_height: int) -> None:
        if max_height < nb_balls:
            raise ValueError("nb_balls can't exceed max_height.")
        self.nb_balls: int = nb_balls
        self.max_height: int = max_height
        self.automaton: nx.DiGraph = nx.DiGraph()
        self.build_automaton()

    def build_automaton(self) -> None:
        for comb in combinations(range(self.max_height), self.nb_balls):
            state_list: list[int] = [0] * self.max_height
            for elem in comb:
                state_list[elem] = 1
            self.automaton.add_node(State(state_list), label=stringify(state_list))

        for state in list(self.automaton.nodes()):
            for _, throw, new_state in state.enumerate_transitions():
                self.automaton.add_edge(state, new_state, throw=throw, label=str(throw))
