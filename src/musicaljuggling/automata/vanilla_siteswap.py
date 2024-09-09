import networkx as nx
from itertools import combinations
from typing import Iterable, NamedTuple, TypeVar, Literal
from automata.fa.nfa import NFA

T = TypeVar('T')

def stringify(iter: Iterable[T]) -> str:
    return "".join(str(elem) for elem in iter)


class State(tuple[int]):
    def shift_state(self) -> "State":
        return State(self[(i + 1) % len(self)] for i in range(len(self)))

    def enumerate_transitions(self) -> list["Transition"]:
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

class InitState:
    def enumerate_transitions(self) -> list["Transition"]:
        raise RuntimeError("Not Implemented")

    def __str__(self) -> str:
        return "Init"


def create_vanilla(nb_balls: int, max_height: int) -> NFA:
    states: set[State | InitState] = set()
    input_symbols = {str(i) for i in range(max_height + 1)}

    for comb in combinations(range(max_height), nb_balls):
        state_as_list: list[int] = [0] * max_height
        for elem in comb:
            state_as_list[elem] = 1
        states.add(State(state_as_list))

    transitions: dict[State | InitState, dict[str, set[State | InitState]]] = {
        state: {} for state in states
    }

    for state in states:
        for _, throw, new_state in state.enumerate_transitions():
            transitions[state][str(throw)] = {new_state}

    # Add initial state
    init_state = InitState()
    states.add(init_state)
    transitions[init_state] = {}
    transitions[init_state][""] = states

    return NFA(
        states=states,
        input_symbols=input_symbols,
        transitions=transitions,
        initial_state=init_state,
        final_states=states,
    )


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

if __name__ == "__main__":
    # import automata.base.config as global_config

    # global_config.should_validate_automata = False
    a = create_vanilla(3, 5)
    a.show_diagram()