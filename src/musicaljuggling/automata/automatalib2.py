from typing import AbstractSet, Optional
from automata.fa.dfa import DFA, DFATransitionsT, DFAStateT


class MultiLetterAutomata(DFA):
    _pool = [chr(elem) for elem in [0x1F988, 0x1F984, 0x1F98B]]

    def __init__(
        self,
        *,
        states: AbstractSet[DFAStateT],
        input_symbols: AbstractSet[str],
        transitions: DFATransitionsT,
        initial_state: DFAStateT,
        final_states: AbstractSet[DFAStateT],
        allow_partial: bool = False,
    ):
        self.multiletters: dict[str, str] = {}
        self.singleletters: dict[str, str] = {}
        if len(input_symbols) > len(self._pool):
            raise RuntimeError("Not enough symbols in internal alphabet pool.")
        for i, symbol in enumerate(input_symbols):
            self.multiletters[symbol] = self._pool[i]
            self.singleletters[self._pool[i]] = symbol
        new_input_symbols = {letter for letter in self.multiletters.values()}

        new_transitions: dict[DFAStateT, dict[str, DFAStateT]] = {}
        for state1, tmp_transition in transitions.items():
            new_transitions[state1] = {}
            for symbol, state2 in tmp_transition.items():
                new_transitions[state1][self.multiletters[symbol]] = state2

        super().__init__(
            states=states,
            input_symbols=new_input_symbols,
            transitions=new_transitions,
            initial_state=initial_state,
            final_states=final_states,
            allow_partial=allow_partial,
        )

    def validate(self):
        self._validate_unambiguous_alphabet()
        super().validate()

    def _validate_unambiguous_alphabet(self):
        # TODO
        pass

    def _multi_to_singleletter_word(self, input_str: str) -> str:
        multiletter = ""
        output = ""
        for letter in input_str:
            multiletter += letter
            if multiletter in self.multiletters:
                output += self.multiletters[multiletter]
                multiletter = ""
        if multiletter != "":
            raise RuntimeError(
                f"Can't convert word, unrecognized caracter {multiletter}"
            )
        return output

    def _single_to_multiletter_word(self, input_str: str) -> str:
        output = ""
        for letter in input_str:
            output += self.singleletters[letter]
        return output

    def accepts_input(self, input_str: str) -> bool:
        try:
            input_str = self._multi_to_singleletter_word(input_str)
        except RuntimeError:
            return False
        return super().accepts_input(input_str)