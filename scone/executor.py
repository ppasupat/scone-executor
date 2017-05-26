from scone.state import SconeObject


################################
# Denotation

class SconeDenotation(tuple):
    """A pretty lightweight class representing the intermediate denotation."""
    __slots__ = ()

    def __new__(self, world_state, command_history, execution_stack):
        """Create a new SconeDenotation.

        Args:
            world_state (SconeState): Current states of the objects
            command_history (list[tuple]): List of actions and arguments
            execution_stack (list[object]): Used for building arguments for the next action
        """
        return tuple.__new__(SconeDenotation, (world_state, command_history, execution_stack))

    @property
    def world_state(self):
        return self[0]

    @property
    def command_history(self):
        return self[1]

    @property
    def execution_stack(self):
        return self[2]

    @property
    def utterance_idx(self):
        return len(self[1])


################################
# Executor

class SconeExecutor(object):
    """Stack-based executor for alchemy, scene, and tangrams domains.
    """

    def __init__(self, initial_state, debug=False):
        self.initial_state = initial_state
        self.debug = debug

    def execute(self, y_toks, old_denotation=None):
        """Return the intermediate denotation of the formula.

        Args:
            y_toks (list[Predicate]): the formula fragment to be executed
            old_denotation (Denotation): If specified, continue execution
                from this intermediate denotation.
        Returns:
            Denotation
            The denotation is not finalized.
        Throws:
            Exception if the formula is malformed.
        """
        if not old_denotation:
            denotation = SconeDenotation(self.initial_state, [], [])
        else:
            assert isinstance(old_denotation, tuple)
            denotation = SconeDenotation(
                    old_denotation.world_state,
                    old_denotation.command_history,
                    old_denotation.execution_stack[:])
        if self.debug:
            print 'Executing: {} (old deno: {})'.format(y_toks, denotation)
        for predicate in y_toks:
            denotation = self.apply(predicate.name, denotation)
            if self.debug:
                print predicate, denotation
        return denotation

    def execute_predicate(self, predicate, old_denotation=None):
        if not old_denotation:
            denotation = SconeDenotation(self.initial_state, [], [])
        else:
            assert isinstance(old_denotation, tuple)
            denotation = SconeDenotation(
                    old_denotation.world_state,
                    old_denotation.command_history,
                    old_denotation.execution_stack[:])
        return self.apply(predicate.name, denotation)

    STACK_NOT_EMPTY = ValueError('Cannot finalize: Stack not empty')

    def finalize(self, denotation):
        """Return the finalized denotation as SconeState.
        Return None if the denotation cannot be finalized.

        For rlong domain, a denotation can be finalized if the stack is empty.
        The result will be a list of a single SconeValue.
        """
        if denotation.execution_stack:
            raise SconeExecutor.STACK_NOT_EMPTY
        return denotation.world_state

    ################################
    # Apply

    def apply(self, name, denotation):
        """Return a new denotation.

        The execution stack can be modified directly.
        But the world state and command history cannot be modified directly;
        a new Denotation object must be created.
        This happens only when an action is performed.

        Args:
            name (str): The next predicate name
            denotation (SconeDenotation): Current denotation
        Returns:
            SconeDenotation
            can be the same object as the input argument
            if only the execution stack is modified
        """
        if len(name) == 1 and name[0].isalpha():
            # Color: Push onto the stack
            denotation.execution_stack.append(name)
            return denotation
        elif name[0] == '-' or name[0].isdigit():
            # Number: Push onto the stack
            denotation.execution_stack.append(int(name))
            return denotation
        elif name[0] == 'X':
            # Fraction: Push onto the stack
            denotation.execution_stack.append(name)
            return denotation
        elif name == 'all-objects':
            # All objects: Push onto the stack
            denotation.execution_stack.append(denotation.world_state.all_objects)
            return denotation
        elif name[0] == 'P':
            # Property: Join with the value
            value = denotation.execution_stack.pop()
            result = denotation.world_state.apply_join(value, name[1:])
            assert result, 'Empty result'
            denotation.execution_stack.append(result)
            return denotation
        elif name[0] == 'D':
            # Double-Property: Join with the values
            value2 = denotation.execution_stack.pop()
            value1 = denotation.execution_stack.pop()
            result = denotation.world_state.apply_double_join(
                    value1, value2, name[1:])
            assert result, 'Empty result'
            denotation.execution_stack.append(result)
            return denotation
        elif name[0] == 'A':
            # Perform action
            new_state, history_entry = denotation.world_state.apply_action(
                    name[1:], denotation.execution_stack)
            return SconeDenotation(new_state,
                    denotation.command_history + [history_entry],
                    denotation.execution_stack)
        elif name == 'index':
            # Perform indexing on a list of objects
            number = denotation.execution_stack.pop()
            assert isinstance(number, int)
            objects = denotation.execution_stack.pop()
            assert isinstance(objects, list)
            if number > 0:
                # Because the LF uses 1-based indexing
                denotation.execution_stack.append(objects[number - 1])
            else:
                # Negative indices: count from the right
                denotation.execution_stack.append(objects[number])
            return denotation
        elif name[0] == 'H':
            # History slot
            number = denotation.execution_stack.pop()
            assert isinstance(number, int)
            # Pull out the argument
            command = denotation.command_history[
                    number - 1 if number > 0 else number]
            if name == 'H0':
                # Get the action and execute
                argument = command[0]
                new_state, history_entry = denotation.world_state.apply_action(
                        argument, denotation.execution_stack)
                return SconeDenotation(new_state,
                        denotation.command_history + [history_entry],
                        denotation.execution_stack)
            elif name == 'HUndo':
                # Get the opposite and execute
                argument = denotation.world_state.reverse_action(command[0])
                new_state, history_entry = denotation.world_state.apply_action(
                        argument, denotation.execution_stack)
                return SconeDenotation(new_state,
                        denotation.command_history + [history_entry],
                        denotation.execution_stack)
            else:
                # Just push onto the stack
                argument = command[int(name[1:])]
                if not isinstance(argument, (int, str)):
                    assert isinstance(argument, SconeObject)
                    argument = denotation.world_state.resolve_argument(argument)
                denotation.execution_stack.append(argument)
                return denotation
        else:
            raise ValueError('Unknown predicate {}'.format(name))


################################
# Top-down executor


class SconeTopDownExecutor(SconeExecutor):

    def check_argument(self, current_args, next_arg):
        """Check if the next argument is valid.

        Args:
            current_args (list):
                The first item is a function name (str);
                the rest are existing arguments
            next_arg (object):
                The next argument to be added.
        Returns:
            If the argument is invalid, throw an error.
            If the argument is valid, return True if the number of arguments
            matches the number of required arguments, and False otherwise.
        """
        # TODO: Better type checking
        name = current_args[0]
        n = len(current_args)
        if name == 'index':
            return n == 2
        if name[0] == 'H':
            assert isinstance(next_arg, int)
            return n == 1
        return self.initial_state.check_argument(current_args, next_arg)

    def apply(self, name, denotation):
        """Return a new denotation.

        The execution stack can be modified directly.
        But the world state and command history cannot be modified directly;
        a new Denotation object must be created.
        This happens only when an action is performed.

        Args:
            name (str): The next predicate name
            denotation (SconeDenotation): Current denotation
        Returns:
            SconeDenotation
            can be the same object as the input argument
            if only the execution stack is modified
        """
        if len(name) == 1 and name[0].isalpha():
            # Color: Append to the function arguments
            obj = name
            ready = self.check_argument(denotation.execution_stack[-1], obj)
            denotation.execution_stack[-1].append(obj)
        elif name[0] == '-' or name[0].isdigit():
            # Number: Append to the function arguments
            obj = int(name)
            ready = self.check_argument(denotation.execution_stack[-1], obj)
            denotation.execution_stack[-1].append(obj)
        elif name[0] == 'X':
            # Fraction: Append to the function arguments
            obj = name
            ready = self.check_argument(denotation.execution_stack[-1], obj)
            denotation.execution_stack[-1].append(obj)
        elif name == 'all-objects':
            # All objects: Append to the function arguments
            obj = denotation.world_state.all_objects
            ready = self.check_argument(denotation.execution_stack[-1], obj)
            denotation.execution_stack[-1].append(obj)
        elif name[0] == 'A' or name == 'H0' or name == 'HUndo':
            # Action: Push onto the stack
            assert not denotation.execution_stack
            ready = False
            denotation.execution_stack.append([name])
        elif name[0] in ('P', 'D', 'A', 'H') or name == 'index':
            # Function: Push onto the stack
            assert denotation.execution_stack
            self.check_argument(denotation.execution_stack[-1], name)
            ready = False
            denotation.execution_stack.append([name])
        else:
            raise ValueError('Unknown predicate {}'.format(name))
        while ready:
            # Execute the innermost function
            args = denotation.execution_stack.pop()
            name = args[0]
            if name[0] == 'P':
                # Property: Joint with the value
                result = denotation.world_state.apply_join(args[1], name[1:])
                assert result, 'Empty result'
                ready = self.check_argument(denotation.execution_stack[-1], result)
                denotation.execution_stack[-1].append(result)
            elif name[0] == 'D':
                # Double-Property: Join with the values
                result = denotation.world_state.apply_double_join(
                        args[1], args[2], name[1:])
                assert result, 'Empty result'
                ready = self.check_argument(denotation.execution_stack[-1], result)
                denotation.execution_stack[-1].append(result)
            elif name[0] == 'A':
                # Perform action
                new_state, history_entry = denotation.world_state.apply_action(
                        name[1:], args[1:])
                return SconeDenotation(new_state,
                        denotation.command_history + [history_entry],
                        denotation.execution_stack)
            elif name == 'index':
                # Perform indexing on a list of objects
                objects, number = args[1], args[2]
                assert isinstance(objects, list)
                assert isinstance(number, int)
                if number > 0:
                    # Because the LF uses 1-based indexing
                    result = objects[number - 1]
                else:
                    # Negative indices: count from the right
                    result = objects[number]
                ready = self.check_argument(denotation.execution_stack[-1], result)
                denotation.execution_stack[-1].append(result)
            elif name[0] == 'H':
                # History slot
                number = args[1]
                assert isinstance(number, int)
                # Pull out the argument
                command = denotation.command_history[
                        number - 1 if number > 0 else number]
                if name == 'H0':
                    # Get the action and push onto the stack
                    assert not denotation.execution_stack
                    ready = False
                    denotation.execution_stack.append(['A' + command[0]])
                elif name == 'HUndo':
                    # Get the opposite action and push onto the stack
                    assert not denotation.execution_stack
                    ready = False
                    denotation.execution_stack.append(['A' + 
                            denotation.world_state.reverse_action(command[0])])
                else:
                    # Get the argument
                    argument = command[int(name[1:])]
                    if not isinstance(argument, (int, str)):
                        assert isinstance(argument, SconeObject)
                        argument = denotation.world_state.resolve_argument(argument)
                    ready = self.check_argument(denotation.execution_stack[-1], argument)
                    denotation.execution_stack[-1].append(argument)
            else:
                raise ValueError('Unknown predicate {}'.format(name))
        return denotation
