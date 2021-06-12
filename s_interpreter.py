import os
from s_lexer import SadeqLexer, stringifyTokens
from s_parser import SadeqParser, makeTreeHandler


class Interpreter:

    def __init__(self, tree, env):
        self.env = env
        self.walkTree(tree)
        self.currentNode = ""

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
            self.env[node[1]] = self.walkTree(node[2])
            return node[1]

        if node[0] == 'var':
            try:
                return self.env[node[1]]
            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                return -1

        # ===================================================
        # ARRAY CONTROLS
        # ===================================================
        if node[0] == 'list_assign':
            if node[2] is None:
                self.env[node[1]] = []
                return node[1]
            else:
                self.env[node[1]] = []
                for x in node[2]:
                    self.env[node[1]].append(self.walkTree(x))

        if node[0] == 'list_index':
            try:
                return self.env[node[1]][self.walkTree(node[2])]
            except IndexError:
                print("Index Error: index out of bound of array: " + node[1])
                return -1
            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                return -1

        # pop
        if node[0] == 'pop':
            try:
                return self.env[node[1]].pop()
            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                return -1

        # push
        if node[0] == 'push':
            try:
                self.env[node[1]].append(self.walkTree(node[2]))
            except LookupError:
                print("LookupError: Undefined variable '" + node[1] + "' found!")
                return -1

        # ===================================================
        # CONTROL NODES
        # ===================================================
        if node[0] == 'if_stmt':
            result = self.walkTree(node[1])
            if result:
                return self.walkTree(node[2])

        if node[0] == 'if_else_stmt':
            result = self.walkTree(node[1])
            if result:
                return self.walkTree(node[2][1])
            return self.walkTree(node[3][1])

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
            self.env[node[1]] = node[2]

        if node[0] == 'func_call':
            try:
                return self.walkTree(self.env[node[1]])
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
                try:
                    for x in self.env[node[1][2]]:
                        self.env[node[1][1]] = x
                        self.walkTree(node[2])
                except LookupError:
                    print("LookupError: variable not found " + node[1][2])
                    return

        # ===================================================
        # PRINT COMMAND
        # ===================================================
        if node[0] == 'print':
            res = self.walkTree(node[1])
            print(str(res).replace('"', "").replace("'", ''))

    # -------------------------------------------------
    def compareTypes(self, aa, bb):
        return type(aa) == type(bb)
