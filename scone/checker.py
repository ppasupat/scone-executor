class SconeProgramChecker(object):
    """Check whether a partial SCONE program is valid."""

    def __init__(self, max_stack_size=3, action_must_clear_beam=True):
        self._max_stack_size = max_stack_size
        self._action_must_clear_beam = action_must_clear_beam

    def __call__(self, program, denotation):
        """Check whether a partial SCONE program is valid.

        Args:
            program (list[SconePredicate])
            denotation (SconeDenotation)
        Returns:
            boolean
        """
        if (self._max_stack_size
                and len(denotation.execution_stack) > self._max_stack_size):
            return False
        if (self._action_must_clear_beam
                and denotation.execution_stack
                and program[-1].name[0] == 'A'):
            return False
        return True
