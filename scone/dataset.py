from codecs import open

from scone.state import SconeAlchemyState, SconeSceneState, SconeTangramsState, SconeUndogramsState


class DatasetReader(object):

    def __init__(self, filename, domain_name, num_steps_list,
            slice_steps_from_middle):
        """Read a SCONE dataset.

        Args:
            domain_name (str): 'alchemy', 'scene', 'tangrams', or 'undograms'
            filename (str): TSV File to load data from. The file format is
                <id> <initstate> <sentence1> <state1> <sentence2> <state2> ...
            num_steps_list (list[int]): Number of sentences for each example.
                E.g., [2, 3] creates examples from the first 2 or 3 sentences.
                num_steps of -1 will take all utterances.
            slice_steps_from_middle (bool): Whether to also get the sentences
                from the middle of the stories. Setting this to False will only
                get the sentences from the beginning of the stories.
        """
        self._filename = filename
        self._domain_name = domain_name
        if domain_name == 'alchemy':
            self._state_class = SconeAlchemyState
        elif domain_name == 'scene':
            self._state_class = SconeSceneState
        elif domain_name == 'tangrams':
            self._state_class = SconeTangramsState
        elif domain_name == 'undograms':
            self._state_class = SconeUndogramsState
        else:
            raise ValueError('Unknown SCONE domain name: {}'.format(domain_name))

        # Parse num_steps
        if not isinstance(num_steps_list, list):
            assert isinstance(num_steps_list, int)
            num_steps_list = list([num_steps_list])
        self._num_steps_list = num_steps_list

        self._slice_steps_from_middle = slice_steps_from_middle

    @property
    def examples(self):
        """Read examples
        
        Yields: tuples (utterances, init_state, target_state)
            utterances (list[list[unicode]])
            init_state (SconeState)
            target_state (SconeState)
        """
        with open(self._filename, 'r', 'utf8') as fin:
            for line in fin:
                line = line.rstrip('\n').split('\t')
                assert len(line) % 2 == 0
                for num_steps in self._num_steps_list:
                    if num_steps == -1:
                        # Maximum number of steps
                        num_steps = len(line) / 2 - 1
                    start_idx = 1
                    while start_idx + 2 * num_steps < len(line):
                        utterances = [utterance.split() for utterance in
                                line[start_idx+1:start_idx+2*num_steps:2]]
                        init_state = self._state_class.from_raw_string(
                                line[start_idx])
                        target_state = self._state_class.from_raw_string(
                                line[start_idx+2*num_steps])
                        yield (utterances, init_state, target_state)
                        if not self._slice_steps_from_middle:
                            break
                        start_idx += 2
