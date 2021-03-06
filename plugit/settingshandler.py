"""
Adds or updates ``varname = value`` assignment statements in either files or
strings that contain valid Python syntax.

The intended use is from applications that need to update settings files
automatically.

Based on lib2to3 tests. Some insight of lib2to3 workings came from Pythoscope
source.
"""

from __future__ import with_statement

from lib2to3 import pygram, pytree
from lib2to3.pgen2 import driver
from lib2to3.pygram import python_symbols as symbols
from lib2to3.pgen2 import token
from lib2to3.pytree import Node, Leaf

from plugit.exceptions import SettingsError

# node factories

Newline = lambda: Leaf(token.NEWLINE, "\n")
Comma = lambda: Leaf(token.COMMA, ',')
Value = lambda value, prefix: Leaf(token.STRING, repr(value),
            prefix=prefix)
AssignStatement = lambda name, value: Node(symbols.expr_stmt,
        [Leaf(token.NAME, name),
         Leaf(token.EQUAL, '=', prefix=' '),
         Value(value, prefix=' '),
         Newline()])


class SettingsStringUpdater(object):
    """
    Base class that implements node tree parsing and updating.
    Handles strings.
    """
    def __init__(self, source):
        """
        Parses `source` to a node tree.

        :param source: a string with Python source
        """
        drv = driver.Driver(pygram.python_grammar, pytree.convert)
        tree = self._parse_func(drv)(source)
        if not isinstance(tree, Node):
            raise SettingsError('Invalid settings: no nodes')
        self.root = tree
        self.changed = False

    @property
    def result(self):
        return str(self.root)

    def update(self, new_settings={}, append_settings={},
            create_if_missing=False):
        """
        Updates the settings. Either of the arguments is optional, but at
        least one should be present. The arguments have to be dictionaries
        with configuration variable name/value pairs. The names should be
        uppercase strings (this is not enforced though).

        :param new_settings: a dictionary with new settings, will create new
            statemens in the form ``NAME = repr(value)``
        :param append_settings: a dictionary of values to add to existing
            configuration variables, whose names are given in keys
        :param create_if_missing: if any configuration variable given in
            `append_settings` is missing, create it, otherwise throw
        """
        node_names = new_settings.keys() + append_settings.keys()
        node_dict = find_assignment_nodes(self.root, node_names)
        for name, value in new_settings.iteritems():
            if name in node_dict:
                raise SettingsError("Variable '%s' already present in settings"
                        % name)
            self.root.append_child(AssignStatement(name, value))
            self.changed = True
        for name, value in append_settings.iteritems():
            if name not in node_dict:
                if create_if_missing:
                    self.root.append_child(AssignStatement(name, value))
                    self.changed = True
                else:
                    raise SettingsError("Variable '%s' missing from settings"
                            % name)
            else:
                append_to_assignment_node(node_dict[name], value)
                self.changed = True

    def _parse_func(self, drv):
        return drv.parse_string


class SettingsFileUpdater(SettingsStringUpdater):
    """
    Handles settings files.
    """
    def __init__(self, filename):
        """
        Parses the contents of `filename` to a node tree.

        :param filename: a file with Python source
        """
        super(SettingsFileUpdater, self).__init__(filename)
        self.filename = filename

    def save(self, filename=None):
        """
        Saves the modified settings back to either the original file
        or a new file. If the node tree is unmodified and no new file name
        given, takes no action.

        :param filename: the new file name to save the modified settings to
        """
        if filename is None and not self.changed:
            return False

        if filename is None:
            filename = self.filename
        with open(filename, 'w') as f:
            f.write(self.result)
        return True

    def _parse_func(self, drv):
        return drv.parse_file


def find_assignment_nodes(tree, names):
    """
    Find assignment statements matching any variable name in `names` in node
    tree `tree`.

    :param names: the list of variable names to find
    :param tree: the node tree
    :return: a dictionary with name/node mapping
    """
    name_patterns = [(pytree.LeafPattern(token.NAME, name),) for name in names]
    lhs_pattern = pytree.NodePattern(symbols.expr_stmt,
            (pytree.WildcardPattern(name_patterns, min=1, max=1),
                pytree.LeafPattern(token.EQUAL, '='),
                pytree.WildcardPattern()), name='match')
    m = {}
    result = {}
    for node in tree.children:
        if (node.type == symbols.simple_stmt
                and lhs_pattern.match(node.children[0], m)):
            result[m['match'].children[0].value] = m['match']
    return result


def append_to_assignment_node(node, value):
    """
    Append `value` to `node` that contains an assignment statement. If
    `node` is a dict node, `value` has to be a dict as well. The dict node
    will be updated with key/value pairs from `value` in this case.

    :param node: the node to be updated
    :param value: the value to be appended to `node`
    """

    assert node.type == symbols.expr_stmt
    atom = node.children[2]
    if atom.type != symbols.atom:
        raise SettingsError("Not a container definition (expression's third "
                "node is not an atom): %s\nCan append only to containers "
                "(dicts or lists)" % str(node))
    # atom can be any of the following:
    # 1. empty
    # Node(atom, [Leaf(26, '{'), Leaf(27, '}')])
    # 2. single element
    # Node(atom, [Leaf(9, '['), Leaf(3, '"a"'), Leaf(10, ']')])
    # 3. multiple elements
    # Node(atom, [Leaf(9, '['), Node(listmaker,
    #    [Leaf(3, '"a"'), Leaf(12, ','), Leaf(3, '"b"')]), Leaf(10, ']')])

    if isinstance(atom.children[1], Node):
        _append_to_node_expression(atom.children[1], value,
                node.children[0].value)
    else:
        _append_to_leaf_expression(atom, value,
                node.children[0].value)


def _append_to_node_expression(container, value, setting):
    if not container.type in (symbols.testlist_gexp, symbols.listmaker,
            symbols.dictsetmaker):
        raise SettingsError("%s: unknown container type (%s). Can append only "
                "to containers (dicts or lists)." % (setting, container.type))

    last_leaf = container.children[-1]
    assert isinstance(last_leaf, Leaf)
    prefix = _find_whitespace(last_leaf)

    if last_leaf.type != token.COMMA:
        container.append_child(Comma())

    if (container.type == symbols.testlist_gexp
            or container.type == symbols.listmaker):
        _append_to_list(container, value, prefix)
    elif container.type == symbols.dictsetmaker:
        # assume it is a dict, not a set
        _append_to_dict(container, value, prefix, setting)

def _append_to_leaf_expression(atom, value, setting):
    first_leaf = atom.children[0]
    prefix = '\n    '
    atom.insert_child(1, Node(symbols.simple_stmt, []))
    if first_leaf.type == token.LSQB or first_leaf.type == token.LPAR:
        _append_to_list(atom.children[1], value, prefix)
    elif first_leaf.type == token.LBRACE:
        _append_to_dict(atom.children[1], value, prefix, setting)

def _append_to_list(node, value, prefix):
    node.append_child(Value(value, prefix))
    node.append_child(Comma())

def _append_to_dict(node, value, prefix, setting):
    if not isinstance(value, dict):
        raise ValueError("Can append only dict values to dict settings "
                "(setting '%s' is a dict, value %s is not)"
                % (setting, repr(value)))
    for key, val in value.iteritems():
        node.append_child(Value(key, prefix))
        node.append_child(Leaf(token.COLON, ':'))
        node.append_child(Value(val, prefix=' '))
        node.append_child(Comma())

def _find_whitespace(l):
    """ Discover whitespace used in container definition. """
    l = l.get_prev_sibling()
    ret = ''
    while l and l.type != token.COMMA:
        ret = l.prefix
        l = l.get_prev_sibling()
    return ret
