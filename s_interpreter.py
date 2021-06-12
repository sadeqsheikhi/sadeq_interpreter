import sys
from functools import reduce  # forward compatibility for Python 3
import operator
from pydash import set_, get, unset


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
            self.setInDict(self.env, holder + [node[1]], res)
            return node[1]

        if node[0] == 'var':
            try:
                # search for var from current to top
                nested = self.currentNode[:]
                while len(nested) > 0:
                    value = self.getFromDict(self.env, nested)

                    if value is None:
                        raise LookupError

                    if node[1] not in value:
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
                self.setInDict(self.env, self.currentNode + [node[1]], [])
                return node[1]
            else:
                holder = []
                for x in node[2]:
                    holder.append(self.walkTree(x))
                self.setInDict(self.env, self.currentNode + [node[1]], holder)

        if node[0] == 'list_index':
            try:
                holder = self.getFromDict(self.env, self.currentNode + [node[1]])[self.walkTree(node[2])]
            except IndexError:
                print("Index Error: index out of bound of array: " + node[1])
                return -1
            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                return -1

        # pop
        if node[0] == 'pop':
            try:
                popped = self.getFromDict(self.env, self.currentNode + [node[1]])
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

        # push
        if node[0] == 'push':
            try:
                pushed = self.getFromDict(self.env, self.currentNode + [node[1]])
                if pushed is None:
                    raise LookupError
                elif not isinstance(pushed, list):
                    raise TypeError
                pushed.append(self.walkTree(node[2]))

            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                exit()

            except TypeError:
                print("TypeError: push method is only defined for list type")
                exit()

        # ===================================================
        # CONTROL NODES
        # ===================================================
        if node[0] == 'if_stmt':
            result = self.walkTree(node[1][1])
            if result:
                return self.walkTree(node[1][2])
            else:
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
            self.setInDict(self.env, self.currentNode + [node[1]], {'%def%': node[3]})
            self.setInDict(self.env, self.currentNode + [node[1]] + ['%pars%'], tuple(node[2]))
            return

        if node[0] == 'func_call':
            try:
                self.currentNode.append(node[1])
                definition = self.getFromDict(self.env, self.currentNode + ['%def%'])
                parameters = self.getFromDict(self.env, self.currentNode + ['%pars%'])

                # comparing parameters satisfaction
                if len(parameters) is not len(node[2]):
                    print('ParameterError: Given parameters don\'t match inputs')
                    exit()
                else:
                    for i in range(len(parameters)):
                        self.setInDict(self.env, self.currentNode + [parameters[i]], self.walkTree(node[2][i]))

                res = self.walkTree(definition)

                # deleting from scope
                scope = self.getFromDict(self.env, self.currentNode)
                self.setInDict(self.env, self.currentNode, {'%def%': scope['%def%'], '%pars%': scope['%pars%']})
                self.currentNode.pop()
                return res

            except LookupError:
                print("LookupError -> Undefined function '%s'" % node[1])
                return -1

        # ===================================================
        # EXPRESSIONS
        # ===================================================
        if node[0] == '+':
            res1 = self.walkTree(node[1])
            res2 = self.walkTree(node[2])
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
                loop_setup = self.walkTree(node[1])

                loop_count = self.env[loop_setup[0]]
                loop_limit = loop_setup[1]

                for i in range(loop_count + 1, loop_limit + 1):
                    res = self.walkTree(node[2])
                    # if res is not None:
                    #     print(res)
                    self.env[loop_setup[0]] = i
                del self.env[loop_setup[0]]

        if node[0] == 'fori_loop_setup':
            return self.walkTree(node[1]), self.walkTree(node[2])

        # ===================================================
        # FOR EACH LOOP
        # ===================================================
        if node[0] == 'foreach_loop':
            if node[1][0] == 'foreach_loop_setup':
                self.currentNode.append("foreach")
                try:
                    for x in self.env[node[1][2]]:
                        self.setInDict(self.env, self.currentNode + [node[1][1]], x)
                        self.walkTree(node[2])

                except LookupError:
                    print("LookupError: variable not found " + node[1][2])
                    sys.exit()
                self.deleteFromDict(self.env, self.currentNode)
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

    # -------------------------------------------------
    def getFromDict(self, dataDict, mapList):
        return get(dataDict, mapList)

    def setInDict(self, dataDict, mapList, value):
        return set_(dataDict, mapList, value)

    def deleteFromDict(self, dataDict, mapList):
        unset(dataDict, mapList)
