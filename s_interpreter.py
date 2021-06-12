import sys
from pydash import set_, get, unset


def getFromDict(dataDict, mapList):
    return get(dataDict, mapList)


def setInDict(dataDict, mapList, value):
    return set_(dataDict, mapList, value)


def deleteFromDict(dataDict, mapList):
    unset(dataDict, mapList)


class Interpreter:

    def __init__(self, tree, env):
        self.env = env
        self.currentNode = []
        self.walkTree(tree)

    def walkTree(self, node):

        # for adjacent statements
        if isinstance(node, list):
            for x in node:
                self.walkTree(x)

        # ===================================================
        # BASE Nodes
        # ===================================================
        # IF NODES IS NONE
        if node is None:
            return None

        if node[0] == 'num':
            return node[1]

        if node[0] == 'float':
            return node[1]

        if node[0] == 'str':
            return node[1]

        if node[0] == 'var_assign':
            holder = self.currentNode
            res = self.walkTree(node[2])
            setInDict(self.env, holder + [node[1]], res)
            return node[1]

        # ---------------------
        # getting variable values based on scope hierarchy
        if node[0] == 'var':
            try:
                # search for var from current to top
                nested = self.currentNode[:]
                while len(nested) > 0:
                    value = getFromDict(self.env, nested)

                    if value is None:
                        nested.pop()

                    elif node[1] not in value:
                        nested.pop()

                    else:
                        return value[node[1]]
                return self.env[node[1]]

            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                exit()

        # ===================================================
        # ARRAY CONTROLS
        # ===================================================
        if node[0] == 'list_assign':
            if node[2] is None:
                setInDict(self.env, self.currentNode + [node[1]], [])
                return node[1]
            else:
                holder = []
                for x in node[2]:
                    holder.append(self.walkTree(x))
                setInDict(self.env, self.currentNode + [node[1]], holder)

        # ---------------------
        # getting index like some_array[3]
        if node[0] == 'list_index':
            try:
                holder = self.walkTree(('var', node[1]))

                # ckeck if holder is list
                if not isinstance(holder, list):
                    print('Index Error: only var of type list can be accessed by index')
                    exit()

                holder = holder[self.walkTree(node[2])]
                return holder

            except IndexError:
                print("Index Error: index out of bound of array: " + node[1])
                return -1
            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                return -1

        # ---------------------
        # pop from list
        if node[0] == 'pop':
            try:
                popped = getFromDict(self.env, self.currentNode + [node[1]])
                if popped is None:
                    raise LookupError
                elif not isinstance(popped, list):
                    raise TypeError
                return popped.pop()

            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                return -1
            except TypeError:
                print("TypeError: pop method is only defined for list type")
                exit()

        # ---------------------
        # push for list
        if node[0] == 'push':
            try:
                pushed = self.walkTree(('var', node[1]))
                if pushed is None:
                    raise LookupError
                elif not isinstance(pushed, list):
                    raise TypeError
                pushed.append(self.walkTree(node[2]))

            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                exit()

            except TypeError as e:
                print("TypeError: push method is only defined for list type")
                exit()

        # ===================================================
        # IF STATEMENTS
        # ===================================================
        if node[0] == 'if_stmt':
            result = self.walkTree(node[1][1])
            if result:
                return self.walkTree(node[1][2])
            else:
                if node[1][3] is None:
                    return
                for x in node[1][3]:
                    if x[0] == 'else_if':
                        result = self.walkTree(x[1])
                        if result:
                            return self.walkTree(x[2])
                    if x[0] == 'else':
                        return self.walkTree(x[1])

        # ===================================================
        # CONDITIONS
        # ===================================================
        if node[0] == 'condition_==':
            return self.walkTree(node[1]) == self.walkTree(node[2])

        if node[0] == 'condition_!=':
            return self.walkTree(node[1]) != self.walkTree(node[2])

        if node[0] == 'condition_>':
            return self.walkTree(node[1]) > self.walkTree(node[2])

        if node[0] == 'condition_<':
            return self.walkTree(node[1]) < self.walkTree(node[2])

        if node[0] == 'condition_>=':
            return self.walkTree(node[1]) >= self.walkTree(node[2])

        if node[0] == 'condition_<=':
            return self.walkTree(node[1]) <= self.walkTree(node[2])

        # ===================================================
        # FUNCTIONS
        # ===================================================
        if node[0] == 'func_def':
            # setting definition and pars
            setInDict(self.env, self.currentNode + [node[1]], {'%def%': node[3]})
            if node[2] is not None:
                setInDict(self.env, self.currentNode + [node[1]] + ['%pars%'], tuple(node[2]))

        if node[0] == 'func_call':
            try:
                self.currentNode.append(node[1])
                definition = getFromDict(self.env, self.currentNode + ['%def%'])
                parameters = getFromDict(self.env, self.currentNode + ['%pars%'])

                # comparing parameters satisfaction
                if parameters is not None and node[2] is not None:
                    if len(parameters) is not len(node[2]) and isinstance(node[2][0], tuple):
                        print('ParameterError: Given parameters don\'t match inputs')
                        exit()
                    else:
                        if isinstance(node[2][0], tuple):
                            for i in range(len(parameters)):
                                setInDict(self.env, self.currentNode + [parameters[i]], self.walkTree(node[2][i]))
                        else:
                            setInDict(self.env, self.currentNode + [parameters[0]], self.walkTree(node[2]))

                        # set parameters as variables

                self.walkTree(definition)
                res = getFromDict(self.env, self.currentNode + ["%return%"])

                # deleting from scope
                scope = getFromDict(self.env, self.currentNode)
                if scope is not None:
                    if '%pars%' in scope:
                        setInDict(self.env, self.currentNode, {'%def%': scope['%def%'], '%pars%': scope['%pars%']})
                    else:
                        setInDict(self.env, self.currentNode, {'%def%': scope['%def%']})

                    self.currentNode.pop()
                return res

            except LookupError as e:
                print("LookupError -> Undefined function '%s'" % node[1])
                return -1

        if node[0] == 'return':
            res = self.walkTree(node[1])
            setInDict(self.env, self.currentNode + ['%return%'], res)
            return res

        # ===================================================
        # EXPRESSIONS
        # ===================================================
        if node[0] == '+':
            res1 = self.walkTree(node[1])
            res2 = self.walkTree(node[2])

            # type checking
            if isinstance(res1, str):
                if isinstance(res2, (int, float)):
                    print(f"Type Error: Cannot do arithmetic operation On Type {type(res1)} and {type(res2)}")
                    return -1
            elif isinstance(res2, str):
                if isinstance(res1, (int, float)):
                    print(f"Type Error: Cannot do arithmetic operation On Type {type(res1)} and {type(res2)}")
                    return -1

            return res1 + res2

        elif node[0] == '-':
            res1 = self.walkTree(node[1])
            res2 = self.walkTree(node[2])
            if isinstance(res1, str) or isinstance(res2, str):
                print(f'Type Error: cannot do subtraction of string type')
                return -1
            return res1 - res2

        elif node[0] == '*':
            res1 = self.walkTree(node[1])
            res2 = self.walkTree(node[2])
            if isinstance(res1, str) or isinstance(res2, str):
                print(f'Type Error: cannot do subtraction of string type')
                return -1
            return res1 * res2

        elif node[0] == '/':
            res1 = self.walkTree(node[1])
            res2 = self.walkTree(node[2])
            if isinstance(res1, str) or isinstance(res2, str):
                print(f'Type Error: cannot do subtraction of string type')
                return -1
            return res1 / res2

        elif node[0] == '%':
            res1 = self.walkTree(node[1])
            res2 = self.walkTree(node[2])
            if type(res1) == str or type(res2) == str:
                print(f'Type Error: cannot do subtraction of string type')
                return -1
            return res1 % res2

        # ===================================================
        # FOR I LOOP
        # ===================================================
        if node[0] == 'fori_loop':
            if node[1][0] == 'fori_loop_setup':
                self.currentNode.append("fori")

                try:
                    # set variable i to the database
                    self.walkTree(node[1][1])

                    # get the limit of the loop
                    limit = self.walkTree(node[1][2])

                    # get the iterator
                    iterator = self.walkTree(('var', node[1][1][1]))

                    # check if the loop is valid
                    if not isinstance(limit, int):
                        print("TypeError: Cannot iterate of variable type: " + type(limit))
                        exit()

                    # main logic of the loop
                    for iterator in range(iterator, limit):
                        setInDict(self.env, self.currentNode + [node[1][1][1]], iterator)
                        self.walkTree(node[2])

                except LookupError as e:
                    if isinstance(node[1][2], str):
                        print("LookupError: variable not found " + node[1][2])
                    exit()

                deleteFromDict(self.env, self.currentNode)
                self.currentNode.pop()

        # ===================================================
        # FOR EACH LOOP
        # ===================================================
        if node[0] == 'foreach_loop':
            if node[1][0] == 'foreach_loop_setup':
                self.currentNode.append("foreach")
                try:

                    # for loop is only for list and str
                    if not isinstance(node[1][2], (list, str)):
                        print("TypeError: foreach loop is only for list or string type")
                        exit()

                    for x in self.walkTree(('var', node[1][2])):
                        setInDict(self.env, self.currentNode + [node[1][1]], x)
                        self.walkTree(node[2])

                except LookupError:
                    print("LookupError: variable not found " + node[1][2])
                    sys.exit()

                deleteFromDict(self.env, self.currentNode)
                self.currentNode.pop()

        # ===================================================
        # PRINT COMMAND
        # ===================================================
        if node[0] == 'print':
            res = self.walkTree(node[1])
            print(str(res).replace('"', "").replace("'", ''))

        # ===================================================
        # LEN FOR STRINGS AND LISTS
        # ===================================================
        if node[0] == 'len':
            res = self.walkTree(node[1])
            if isinstance(res, str) or isinstance(res, list):
                return len(res)
            else:
                print('TypeError: len() only accepts list and strings')
                exit()
