import networkx as nx
from itertools import product
from dataclasses import dataclass
from functools import cached_property
from .utils import left_shift, find_indices
from typing import NamedTuple, Optional, Type
from collections import deque

# TODO : reverse generation ? More efficient if from end of music.

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

# Première version naive où on essaie toutes les transitions.


@dataclass(frozen=True)
class State:
    hands: tuple[tuple[str, ...], tuple[str, ...]]
    airborn: tuple[str, ...]
    throw_from: int

    @classmethod
    def from_list(
        cls: Type["State"],
        hands: list[list[str]],
        airborn: list[str],
        throw_from: int,
    ) -> "State":
        if len(hands) != 2:
            raise ValueError("hands should have 2 elements.")
        return State((tuple(hands[0]), tuple(hands[1])), tuple(airborn), throw_from)

    # Peut etre renvoyer un set, et avoir une autre fonction "has_caught_balls"
    @cached_property
    def caught_ball(self) -> str:
        return self.airborn[0]

    """@cached_property
    def throwable_balls(self) -> set[str]:
        balls = set()
        if self.caught_ball:
            balls |= set(self.caught_ball)
        if self.throw_from_left:
            balls |= set(self.left_hand)
        else:
            balls |= set(self.right_hand)
        return balls"""

    @cached_property
    def shifted(self) -> "State":
        """Returns the shifted state of the current state, where all balls have fallen one step.
        This does not define a valid transition from the current state, has we haven't yet thrown a ball.
        """
        new_hands = [list(hand) for hand in self.hands]
        new_airborn = left_shift(list(self.airborn), 1)
        if self.airborn[0] != "":
            new_hands[self.throw_from].append(self.airborn[0])
        return State.from_list(new_hands, new_airborn, self.throw_from)

    def transitions(self) -> list["Transition"]:
        new_throw_from = (self.shifted.throw_from + 1) % 2
        if len(self.shifted.hands[self.shifted.throw_from]) == 0:
            return [
                Transition(
                    None,
                    0,
                    State(self.shifted.hands, self.shifted.airborn, new_throw_from),
                )
            ]
        transitions = []
        throw_heights = [i + 1 for i in find_indices(self.shifted.airborn, "")]
        for ball in self.hands[self.throw_from]:
            for height in throw_heights:
                new_hands = [list(new_hand) for new_hand in self.shifted.hands]
                new_airborn = list(self.shifted.airborn)
                new_hands[self.shifted.throw_from].remove(ball)
                new_airborn[height] = ball
                transitions.append(
                    Transition(
                        ball,
                        height,
                        State.from_list(new_hands, new_airborn, new_throw_from),
                    )
                )
        return transitions


# reecrire avec une union de type qui correspondent aux différentes formes de lancers (bruyants, pas de lancer, on attrape juste, et silencieux)
# Renommer shifted state ?
class Transition(NamedTuple):
    ball: Optional[str]
    height: int
    new_state: State


class MusicalAutomaton:
    def __init__(
        self,
        music: list[str],
        max_height: int,
        balls: Optional[list[str]],
        autobuild: bool = True,
    ) -> None:
        self.music = music
        self.max_height = max_height
        if balls is None:
            balls = list(set(music))
        self.balls = balls
        self.automata: nx.DiGraph = nx.DiGraph()
        self.initial_states: list[State] = []
        self.final_states: list[State] = []
        if autobuild:
            pass

    def generate_initial_states(self) -> None:
        for comb in product(range(2), repeat=len(self.balls)):
            hands: list[list[str]] = [[], []]
            for i in comb:
                hands[i].append(self.balls[i])
            # We arbitrarily chose to start from the left hand.
            state = State.from_list(hands, [""] * self.max_height, 0)
            self.automata.add_node(state)
            self.initial_states.append(state)

    def generate_transitions(self) -> None:
        states_to_handle = self.initial_states.copy()
        self.automata.add_nodes_from(states_to_handle)
        # We need to account for the time to throw balls before the music starts.
        extended_music = [""] * self.max_height + self.music
        for i, note in enumerate(extended_music):
            next_states_to_handle: list[State] = []
            for state in states_to_handle:
                if state.caught_ball != note:
                    continue
                for transition in state.transitions():
                    if (
                        i == len(extended_music) - 1
                        and transition.new_state.airborn
                        != tuple([""] * self.max_height) * self.max_height
                    ):
                        continue
                    self.automata.add_edge(
                        state,
                        transition.new_state,
                        ball=transition.ball,
                        height=transition.height,
                        label=f"{transition.ball}{transition.height}",
                    )
            states_to_handle = next_states_to_handle
        self.final_states = states_to_handle

    def bfs(self, sources: list[State], reverse: bool = False) -> set[State]:
        to_process: deque[State] = deque(sources)
        nodes_met = set()
        while len(to_process) != 0:
            node = to_process.popleft()
            neighbours = (
                self.automata.predecessors(node)
                if reverse
                else self.automata.successors(node)
            )
            for nei in neighbours:
                if nei not in nodes_met:
                    nodes_met.add(nei)
                    to_process.append(nei)
        return nodes_met

    def elagate(self) -> None:
        # Checks if every node v of the automaton is both accessible and co-accessible,
        # ie, if there exists u an initial state and w a final state such that u -> v -> w.
        # By construction of the automata states, we know there already exists a path u -> v.
        co_accessible_nodes = self.bfs(self.final_states, reverse=True)
        nodes_to_remove = set(self.automata.nodes) - co_accessible_nodes
        self.automata.remove_nodes_from(nodes_to_remove)
        # Sanity check
        # accessible_nodes = self.bfs(self.final_states, reverse=True)
        # nodes_to_remove = set(self.automata.nodes) - accessible_nodes
        # self.automata.remove_nodes_from(nodes_to_remove)

    # def draw(self):
    #    pass
