# ==========================================================================================
# DRIVER OF THE PROGRAM
# ==========================================================================================
import os

from s_interpreter import Interpreter
from s_lexer import SadeqLexer, readFile, stringifyTokens
from s_parser import SadeqParser, makeTreeHandler

if __name__ == '__main__':
    lexer = SadeqLexer()
    parser = SadeqParser()

    # reading the file
    # ---------------------------------------
    # fileName = input('PARSE FILE ==> ')
    script = readFile('input.sa')

    # tokenizing the input
    # ---------------------------------------
    tokens = lexer.tokenize(script)
    tokenString = stringifyTokens(tokens)
    f = open('OUTPUT\\tokens.txt', "w+")
    f.write(tokenString)
    f.close()

    # parsing and generating AST
    # ---------------------------------------
    tupleTree = parser.parse(lexer.tokenize(script))
    if tupleTree is not None:
        tree = makeTreeHandler(tupleTree)
        os.remove('OUTPUT\\treeRepresentation.txt')

        f = open('OUTPUT\\treeRepresentation.txt', "w+")
        import json
        f.write(json.dumps(tupleTree) + '\n\n\n')
        f.close()

        tree.save2file(filename='OUTPUT\\treeRepresentation.txt', reverse=True)

    # setting up env and execute
    # ---------------------------------------
    env = {}
    Interpreter(tupleTree, env)
