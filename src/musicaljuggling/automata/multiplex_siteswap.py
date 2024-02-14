import networkx as nx
from itertools import combinations
from typing import NamedTuple
from .utils import stringify


class State():
    def shift_state(self) -> "State":
        hands_list = self.copy()
        for hand_state in self:
            hand_new_state = hand_state[(i + 1) % len(hand_state)] for i in range(len(hand_state))
            hands_list.append(hand_new_state)
        return State(hands_list)

    def enumerate_transitions(self) -> list["Transition"]:
        shifted_state = self.shift_state()
        
        for hand in self:
            if hand[0] == 0





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


class MultiplexAutomaton:
    def __init__(self, nb_balls: int, max_height: int, nb_hands: int) -> None:
        if max_height < nb_balls:
            raise ValueError("nb_balls can't exceed max_height.")
        self.nb_balls: int = nb_balls
        self.max_height: int = max_height
        self.nb_hands: int = nb_hands
        self.automaton: nx.DiGraph = nx.DiGraph()
        self.build_automaton()


    def enumerate_states(self):
        for 

    def build_automaton(self) -> None:
        for comb in combinations(range(self.max_height), self.nb_balls):
            state_list: list[int] = [0] * self.max_height
            for elem in comb:
                state_list[elem] = 1
            self.automaton.add_node(State(state_list), label=stringify(state_list))

        for state in list(self.automaton.nodes()):
            for _, throw, new_state in state.enumerate_transitions():
                self.automaton.add_edge(state, new_state, throw=throw, label=str(throw))
