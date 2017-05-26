class SconePredicate(object):
    """A program token.

    Conventions:
    - colors are single characters (y, g, ...)
    - numbers are integers, positive or negative (1, -2, ...)
    - fractions start with X (X1/2, X2/3, ...)
    - properties start with P (PColor, PHatColor, ...)
    - actions start with A (ADrain, AMove, ...)
    - built-in predicates include:
        all-objects, index, argmin, argmax
    - history slots start with H (H0, H1, ...)
    """
    CACHE = {}

    def __new__(cls, name):
        """SconePredicates with the same name are only created once."""
        if name not in cls.CACHE:
            pred = object.__new__(cls, name)
            cls.CACHE[name] = pred
        return cls.CACHE[name]

    def __init__(self, name):
        self._name = name
        self._types = self._compute_types(name)

    @classmethod
    def _compute_types(cls, name):
        assert isinstance(name, str)
        types = []
        if len(name) == 1 and name[0].isalpha():
            types.append(SconePredicateType.COLOR)
        elif name[0] == '-' or name[0].isdigit():
            types.append(SconePredicateType.NUMBER)
        elif name[0] == 'X':
            types.append(SconePredicateType.FRACTION)
        elif name[0] == 'P':
            types.append(SconePredicateType.PROPERTY)
        elif name[0] == 'D':
            types.append(SconePredicateType.DOUBLE_PROPERTY)
        elif name[0] == 'A':
            types.append(SconePredicateType.ACTION)
        elif name in BUILTIN_NAMES:
            types.append(SconePredicateType.BUILTIN)
        elif name[0] == 'H':
            types.append(SconePredicateType.HISTORY_SLOT)
        else:
            raise ValueError('Unknown predicate: {}'.format(name))
        return tuple(types)

    def __eq__(self, other):
        return (isinstance(other, SconePredicate)
                and self._name == other._name)

    def __hash__(self):
        return hash(self._name)

    def __str__(self):
        return self._name
    __repr__ = __str__

    @property
    def name(self):
        """Name of the predicate.

        Returns:
            unicode
        """
        return self._name

    @property
    def types(self):
        """A collection of types.

        Returns:
            tuple[unicode]
        """
        return self._types

    @property
    def types_vector(self):
        """Return the types as a k-hot vector.

        Returns:
            list[boolean]
        """
        return [x in self.types for x in SconePredicateType.ALL_TYPES]


BUILTIN_NAMES = ['all-objects', 'index', 'argmin', 'argmax']

class SconePredicateType(object):
    COLOR = 'color'
    NUMBER = 'number'
    FRACTION = 'fraction'
    PROPERTY = 'property'
    DOUBLE_PROPERTY = 'double_property'
    ACTION = 'action'
    BUILTIN = 'builtin'
    HISTORY_SLOT = 'history_slot'
    ALL_TYPES = (COLOR, NUMBER, FRACTION, PROPERTY, 
            DOUBLE_PROPERTY, ACTION, BUILTIN, HISTORY_SLOT)


################################
# Default predicate lists

ALCHEMY_PREDICATES = [
        SconePredicate(x) for x in [
            'r', 'y', 'g', 'o', 'p', 'b',
            '1', '2', '3', '4', '5', '6', '7',
            '-1',
            'X1/1',
            'PColor',
            'APour', 'AMix', 'ADrain',
            'all-objects', 'index',
            'H0', 'H1', 'H2',
            ]]

SCENE_PREDICATES = [
        SconePredicate(x) for x in [
            'r', 'y', 'g', 'o', 'p', 'b', 'e',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
            '-1',
            'PShirt', 'PHat', 'PLeft', 'PRight', 'DShirtHat',
            'ALeave', 'ASwapHats', 'AMove', 'ACreate',
            'all-objects', 'index',
            'H0', 'H1', 'H2', 'H3',
            ]]

TANGRAMS_PREDICATES = [
        SconePredicate(x) for x in [
            '1', '2', '3', '4', '5',
            '-1',
            'AAdd', 'ASwap', 'ARemove',
            'all-objects', 'index',
            'H0', 'H1', 'H2',
            ]]

UNDOGRAMS_PREDICATES = [
        SconePredicate(x) for x in [
            '1', '2', '3', '4', '5',
            '-1',
            'AAdd', 'ASwap', 'ARemove',
            'all-objects', 'index',
            'H0', 'H1', 'H2', 'HUndo',
            ]]
