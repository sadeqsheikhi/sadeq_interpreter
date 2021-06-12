import os
from sly import Parser
from treelib import Tree
from treelib.exceptions import DuplicatedNodeIdError
from s_lexer import SadeqLexer


class SadeqParser(Parser):
    # =================================================================
    # initializing and precedence
    # =================================================================

    tokens = SadeqLexer.tokens
    # debugfile = 'parser.out'

    # this is used to avoid ambiguity in the grammer
    precedence = (
        ('nonassoc', GRT, SMT, GREQ, SMEQ),  # non-associative operators (wrong: 3 < x < 5)
        ('left', "+", "-"),
        ('left', "*", "/"),
        ('right', UMINUS),  # unary minus operator (ex: -4)
    )

    # flattens adjacent statements
    def flatten(self, S):
        if not S:
            return S
        if isinstance(S[0], list):
            return self.flatten(S[0]) + self.flatten(S[1:])
        return S[:1] + self.flatten(S[1:])

    # defines the staring rule
    start = 'init'

    # ============================================================================================
    # --------------------------------------------------------------------------------------------- GRAMMAR RULES
    # ============================================================================================
    @_('init statement')
    def init(self, p):
        return self.flatten([p.init, p.statement])

    @_('statement')
    def init(self, p):
        return p.statement

    @_('')
    def init(self, p):
        return None

    # ====================================================
    # STATEMENTS
    @_('FOR var_assign TO expr "{" init "}"')
    def statement(self, p):
        return 'fori_loop', ('fori_loop_setup', p.var_assign, p.expr), p.init

    @_('FOREACH ID IN ID "{" init "}"')
    def statement(self, p):
        return 'foreach_loop', ('foreach_loop_setup', p.ID0, p.ID1), p.init

    @_('if_else')
    def statement(self, p):
        return 'if_stmt', p.if_else

    @_('FUNC ID "(" id_list ")" "{" init "}"')
    def statement(self, p):
        return 'func_def', p.ID, p.id_list, p.init

    @_('ID "(" expr_list ")"')
    def statement(self, p):
        return 'func_call', p.ID, p.expr_list

    @_('PRINT "(" expr ")"')
    def statement(self, p):
        return 'print', p.expr

    @_('var_assign')
    def statement(self, p):
        return p.var_assign

    @_('POP "(" ID ")"')
    def statement(self, p):
        return 'pop', p.ID

    @_('PUSH "(" ID "," expr ")"')
    def statement(self, p):
        return 'push', p.ID, p.expr

    # ====================================================
    # IF ELSE STATEMENT
    @_('IF condition "{" init "}" el_if')
    def if_else(self, p):
        return 'if', p.condition, p.init, p.el_if

    @_('ELSE IF condition "{" init "}" el_if')
    def el_if(self, p):
        return self.flatten([('else_if', p.condition, p.init), p.el_if])

    @_('ELSE "{" init "}"')
    def el_if(self, p):
        return 'else', p.init

    @_('')
    def el_if(self, p):
        return None

    # ====================================================
    # CONDITIONS
    @_('expr EQUAL expr',
       'expr NEQUAL expr',
       'expr GRT expr',
       'expr SMT expr',
       'expr GREQ expr',
       'expr SMEQ expr')
    def condition(self, p):
        return f"condition_{p[1]}", p.expr0, p.expr1

    # ====================================================
    # var_assign
    @_('ID ASSIGN expr')
    def var_assign(self, p):
        return 'var_assign', p.ID, p.expr

    @_('ID ASSIGN "[" list_generate "]"')
    def var_assign(self, p):
        return 'list_assign', p.ID, p.list_generate

    # ====================================================
    # id_list
    @_('ID "," id_list')
    def id_list(self, p):
        return self.flatten([p.ID, p.id_list])

    @_('ID')
    def id_list(self, p):
        return p.ID

    @_('')
    def id_list(self, p):
        return None

    # ====================================================
    # list_generate
    @_('expr "," list_generate')
    def list_generate(self, p):
        return self.flatten([p.expr, p.list_generate])

    @_('expr')
    def list_generate(self, p):
        return p.expr

    @_('')
    def list_generate(self, p):
        return None

    # ====================================================
    # expression List
    @_('expr "," expr_list')
    def expr_list(self, p):
        return self.flatten([p.expr, p.expr_list])

    @_('expr')
    def expr_list(self, p):
        return p.expr

    @_('')
    def expr_list(self, p):
        return None

    # ====================================================
    # expressions
    @_('expr "+" expr',
       'expr "-" expr',
       'expr "*" expr',
       'expr "/" expr',
       'expr "%" expr',
       )
    def expr(self, p):
        return p[1], p.expr0, p.expr1

    @_('"-" expr %prec UMINUS')
    def expr(self, p):
        return p.expr

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('ID')
    def expr(self, p):
        return 'var', p.ID

    @_('ID "[" expr "]"')
    def expr(self, p):
        return 'list_index', p.ID, p.expr

    @_('NUMBER')
    def expr(self, p):
        return 'num', p.NUMBER

    @_('FLOAT')
    def expr(self, p):
        return 'float', p.FLOAT

    @_('STRING')
    def expr(self, p):
        return 'str', p.STRING

    @_('POP "(" ID ")"')
    def expr(self, p):
        return 'pop', p.ID

    @_('LEN "(" expr ")"')
    def expr(self, p):
        return 'len', p.expr


# CREATING REPRESENTATION USING TREELIB
# =================================================================
def makeTree(parent, tree, myList):
    # index is used to number the adjacent & similar functions
    index = 0

    for node in myList:

        # base states
        if node is None:
            tree.create_node('none', parent + f' {tree.depth()} ' + str(node), parent)
        elif isinstance(node, (int, str)):
            tree.create_node(node, parent + f' {tree.depth()} ' + str(node), parent)

        # recursively go in depth
        elif isinstance(node[0], str):
            depth = tree.depth(parent)

            try:
                nodeId = parent + f' {depth} ' + node[0]
                tree.create_node(node[0], nodeId, parent)
                makeTree(nodeId, tree, node[1:])

            except DuplicatedNodeIdError:
                '''
                triggers for 2 adjacent & similar nodes
                for example when input is like this
                print('sadeq')
                print('sheikhi')
                '''
                index += 1
                nodeId = parent + f'{depth}' + node[0] + " " + str(index)
                tree.create_node(node[0], nodeId, parent)
                makeTree(nodeId, tree, node[1:])
        else:
            # for nested adjacent nodes
            makeTree(parent, tree, node)


def makeTreeHandler(myList):
    tree = Tree()
    # creating base node
    tree.create_node("PROGRAM", "program")

    '''
    the input functions accepts a list
    if the input is not a list, make it one
    '''
    if not isinstance(myList, list):
        myList = [myList]

    # Recursive function to generate the treelib tree
    makeTree('program', tree, myList)
    return tree