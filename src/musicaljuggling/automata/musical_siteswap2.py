import networkx as nx
from itertools import product
from dataclasses import dataclass
from functools import cached_property
from musicaljuggling.automata.utils import right_shift
from typing import NamedTuple, Optional, Type
from collections import deque
from os.path import exists
from copy import copy, deepcopy

# Second version where we start generation from the end.

"""
Constraints :
- music : the music to be played. A list that states
- max_hand_capacity
- hands_as_heap : Should the hands be seen as a stack (meaning the only balls on a hand have a FIFO structure : only the latest ball can be thrown.
- allow_multiplex
- juggler_as_2_hands or juggler_as_one_hand
- miss_beat_after_synchronous_throw
- table
- forbidden_throw_sequences
- max_height
- allow_silent_catches
- allow multiball catch
- can_hold_balls
- allow_tempo_change

MISSING : constraints on how to catch the balls. For instance, for rythmic balls, higher throws will make them sound different.
Constraints specific to each juggler.
See a juggler as either 2 hands or A vanilla siteswap kind of hand.
"""

"""class Constraints():
    music: Any
    ball_types: Any
    nb_balls
    nb_hands"""


@dataclass(frozen=True)
class State:
    hands: tuple[tuple[str, ...], tuple[str, ...]]
    airborn: tuple[str, ...]
    throw_from: int
    time: int

    @classmethod
    def from_list(
        cls: Type["State"],
        hands: list[list[str]],
        airborn: list[str],
        throw_from: int,
        time: int,
    ) -> "State":
        if len(hands) != 2:
            raise ValueError("hands should have 2 elements.")
        return State(
            (tuple(hands[0]), tuple(hands[1])), tuple(airborn), throw_from, time
        )

    def __repr__(self) -> str:
        string = ""
        string += "X" if len(self.hands[0]) == 0 else "".join(self.hands[0])
        string += "<| " if self.throw_from == 0 else " |>"
        string += "X" if len(self.hands[1]) == 0 else "".join(self.hands[1])
        string += " | "
        string += "".join("X" if elem == "" else elem for elem in self.airborn)
        string += f" | t={self.time}"
        return string

    @cached_property
    def caught_ball(self) -> str:
        return self.airborn[0]

    def back_transitions(self, note: str) -> list["Transition"]:
        #Plus clair en faisant pour airborn une liste avec un elem en plus ?
        old_hands = [list(hand) for hand in self.hands]
        old_throw_from = (self.throw_from + 1) % 2
        old_airborn = right_shift(list(self.airborn))
        old_time = self.time - 1
        
        # First, we handle if we can catch the note that is supposed to happen.
        if note != "":
            # It needs to be in the hand at current time, that caught previously
            if note in self.hands[old_throw_from]:
                old_hands[old_throw_from].remove(note)
                old_airborn[0] = note
            # ...or it was previously thrown with height 1.
            # In that case, there must not be a ball at maximum height
            # as this would result in two throws at once.
            elif note in self.airborn and (self.airborn[-1] == "" or self.airborn[-1] == note):
                old_airborn[self.airborn.index(note)] = ""
                old_airborn[0] = note
                old_state = State.from_list(old_hands, old_airborn, old_throw_from, old_time)
                return [Transition(old_state, self, note, 1)]
            else:
                return []

        # Second, we see if we're required to throw a ball that has reached maximum height.
        if self.airborn[-1] != "":
            old_hands[old_throw_from].append(self.airborn[-1])
            old_state = State.from_list(old_hands, old_airborn, old_throw_from, old_time)
            return [Transition(old_state, self, self.airborn[-1], len(self.airborn))]
        
        # Last, we generate all transitions (doing nothing + all throws)
        old_state = State.from_list(old_hands, old_airborn, old_throw_from, old_time)
        transitions = [Transition(old_state, self, None, 0)]
        for i, ball in enumerate(old_airborn):
            if ball == "":
                continue
            old_hands_tmp = deepcopy(old_hands)
            old_hands_tmp[old_throw_from].append(ball)
            old_airborn_tmp = copy(old_airborn)
            old_airborn_tmp[i] = ""
            old_state = State.from_list(old_hands_tmp, old_airborn_tmp, old_throw_from, old_time)
            transitions.append(Transition(old_state, self, ball, i))

        return transitions


# reecrire avec une union de type qui correspondent aux différentes formes de lancers (bruyants, pas de lancer, on attrape juste, et silencieux)
# Renommer shifted state ?
class Transition(NamedTuple):
    old_state: State
    new_state: State
    ball: Optional[str]
    height: int


class MusicalAutomaton:
    def __init__(
        self,
        music: list[str],
        max_height: int,
        balls: Optional[list[str]] = None,
        autobuild: bool = True,
    ) -> None:
        self.music = music
        self.max_height = max_height
        if balls is None:
            balls = list(set(music) - set([""]))
        self.balls = balls
        self.automaton: nx.DiGraph[State] = nx.DiGraph()
        self.initial_states: list[State] = []
        self.final_states: list[State] = []
        if autobuild:
            self.build_automaton()

    def build_automaton(self) -> None:
        # Generation is done from the end of the music to the beginning.
        self.build_final_states()
        self.build_back_transitions()
        self.elagate()

    # Attention à la logique si on appelle plusieurs fois cette fonction.
    # CHanger le type de retour pour retourner la liste plutôt que de muter ?
    def build_final_states(self) -> None:
        balls_to_consider = copy(self.balls)
        if self.music[-1] != "":
            balls_to_consider.remove(self.music[-1])
        airborn = [""] * self.max_height
        airborn[0] = self.music[-1]
        for comb in product(range(2), repeat=len(balls_to_consider)):
            hands: list[list[str]] = [[], []]
            for ball_idx, hand_idx in enumerate(comb):
                hands[hand_idx].append(balls_to_consider[ball_idx])
            # We arbitrarily choose to catch the first ball from the left hand.
            state = State.from_list(hands, airborn, (len(self.music) - 1) % 2, len(self.music) - 1)
            self.final_states.append(state)

    def build_back_transitions(self) -> None:
        # A final state is a state at the end of the music.
        # An initial state is a state when the first note is caught 
        states_to_handle: set[State] = set(self.final_states)
        self.automaton.add_nodes_from(states_to_handle)
        for i in range(len(self.music) - 2, -1, -1):
            next_states_to_handle: set[State] = set()
            for state in states_to_handle:
                for transition in state.back_transitions(self.music[i]):
                    self.automaton.add_edge(
                        transition.old_state,
                        transition.new_state,
                        ball=transition.ball,
                        height=transition.height,
                        label=f"{transition.ball if transition.ball else ""}{transition.height}",
                    )
                    next_states_to_handle.add(transition.old_state)
            states_to_handle = next_states_to_handle
        # All initial states are the ones we obtain
        self.final_states = list(states_to_handle)

    def bfs(self, sources: list[State], reverse: bool = False) -> set[State]:
        to_process: deque[State] = deque(sources)
        nodes_met = set(sources)
        while len(to_process) != 0:
            node = to_process.popleft()
            neighbours = (
                self.automaton.predecessors(node)
                if reverse
                else self.automaton.successors(node)
            )
            for nei in neighbours:
                if nei not in nodes_met:
                    nodes_met.add(nei)
                    to_process.append(nei)
        return nodes_met

    def elagate(self) -> None:
        # Checks if every node v of the automaton is both accessible and co-accessible,
        # ie, if there exists u an initial state and w a final state such that u -> v -> w.
        # By construction of the automaton states, we know there already exists a path v -> w.
        accessible_nodes = self.bfs(self.initial_states, reverse=False)
        nodes_to_remove = set(self.automaton.nodes) - accessible_nodes
        self.automaton.remove_nodes_from(nodes_to_remove)
        # Sanity check
        # accessible_nodes = self.bfs(self.final_states, reverse=True)
        # nodes_to_remove = set(self.automaton.nodes) - accessible_nodes
        # self.automaton.remove_nodes_from(nodes_to_remove)

    def draw(self, path: Optional[str] = None, notebook: bool = False) -> None:
        if not notebook and path is None:
            raise ValueError("Either notebook should be true, or you should provide a path to store the drawing")
        save = path is not None
        if not save:
            path = "_tmp.svg"
            while exists(path):
                path = "_" + path
        aut_to_draw = nx.nx_agraph.to_agraph(self.automaton) #type: ignore
        aut_to_draw.layout("dot")
        aut_to_draw.draw(path)
        if notebook:
            from IPython.display import SVG, display
            display(SVG(path))
        #if not save:
        #    remove(path)


if __name__ == "__main__":
    au_clair_de_la_lune = ["C", "C", "C", "D", "E", "", "D", "", "C", "E", "D", "D", "C"]
    a = MusicalAutomaton(au_clair_de_la_lune, 5)
    print("fini")
