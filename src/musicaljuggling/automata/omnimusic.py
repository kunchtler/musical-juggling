from musicaljuggling.automata.musical_siteswap_backwards import State
import networkx as nx
from os.path import exists
from typing import Optional
from itertools import product, permutations


class Omnimusic:
    def __init__(
        self, max_height: int, balls: list[str], autobuild: bool = True
    ) -> None:
        self.max_height = max_height
        self.balls = balls
        # We assume all states are initial and final.
        self.automaton: nx.DiGraph[State] = nx.DiGraph()

    def build_automaton(self) -> None:
        self.build_states()
        self.build_transitions()

    def build_states(self) -> None:
        # Generates all states of balls in the air / in hands
        for ball_attribution in product(range(2), repeat=len(self.balls)):
            balls_in_hand = []
            balls_airborn = []
            for ball_idx, place in enumerate(ball_attribution):
                if place == 0:
                    balls_in_hand.append(self.balls[ball_idx])
                if place == 1:
                    balls_airborn.append(self.balls[ball_idx])

            hands_possibilities = []
            airborn_possibilities = []
            for hand_attribution in product(range(2), repeat=len(balls_in_hand)):
                hands: list[set[str]] = [set(), set()]
                for ball_idx, hand in enumerate(hand_attribution):
                    hands[hand].add(balls_in_hand[ball_idx])
                hands_possibilities.append(hands)
            for airborn_attribution in permutations(
                range(self.max_height), len(balls_airborn)
            ):
                airborn = [""] * self.max_height
                for ball_idx, height in enumerate(airborn_attribution):
                    airborn[height] = balls_airborn[ball_idx]
                airborn_possibilities.append(airborn)

            for hands, airborn in product(hands_possibilities, airborn_possibilities):
                self.automaton.add_node(State.from_list(hands, airborn, 0))
                self.automaton.add_node(State.from_list(hands, airborn, 1))

    def build_transitions(self) -> None:
        nb_nodes_pre = self.automaton.number_of_nodes()
        for state in list(self.automaton.nodes):
            for transition in state.all_notes_back_transitions():
                self.automaton.add_edge(
                        transition.old_state,
                        transition.new_state,
                        ball=transition.ball,
                        height=transition.height,
                        label=f"{transition.ball if transition.ball else ""}{transition.height}",
                    )
        nb_nodes_post = self.automaton.number_of_nodes()
        assert(nb_nodes_pre == nb_nodes_post)
    
    def draw(self, path: Optional[str] = None, notebook: bool = False) -> None:
        if not notebook and path is None:
            raise ValueError(
                "Either notebook should be true, or you should provide a path to store the drawing"
            )
        save = path is not None
        if not save:
            path = "_tmp.svg"
            while exists(path):
                path = "_" + path
        aut_to_draw = nx.nx_agraph.to_agraph(self.automaton)  # type: ignore
        aut_to_draw.layout("fdp")
        aut_to_draw.draw(path)
        if notebook:
            from IPython.display import SVG, display
            display(SVG(path))

if __name__ == "__main__":
    test = Omnimusic(3, ["A", "B"], autobuild=False)
    test.build_states()
    test.build_transitions()
    print("fini")
