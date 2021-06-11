from sly import Lexer


class SadeqLexer(Lexer):
    # =================================================================
    # DEFINING TOKENS
    # =================================================================

    # Set of token names.   This is always required
    tokens = {ID, NUMBER, STRING, FLOAT,
              EQUAL, NEQUAL, GRT, SMT, GREQ, SMEQ,
              ASSIGN,
              IF, ELSE, FOR, FOREACH, TO, IN, FUNC,
              PRINT}

    literals = {'+', '-', '*', '/', '(', ')', '{', '}', ";", "%", "[", "]", ","}

    # String containing ignored characters between tokens
    ignore = ' \t'

    # Regular expression rules for tokens
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    STRING = r'[\"|\'].*?[\"|\']'

    EQUAL = r'=='
    NEQUAL = r'!='
    GREQ = r'>='
    SMEQ = r'<='
    GRT = r'>'
    SMT = r'<'

    ASSIGN = r'='

    # KEYWORDS
    ID['if'] = IF
    ID['else'] = ELSE
    ID['for'] = FOR
    ID['foreach'] = FOREACH
    ID['to'] = TO
    ID['in'] = IN
    ID['function'] = FUNC
    ID['print'] = PRINT

    @_(r'\d+\.\d+')
    def FLOAT(self, t):
        t.value = float(t.value)
        return t

    # catching numbers and turning them to python ints
    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    # Line number tracking
    @_(r'\n+')
    def newline(self, t):
        self.lineno = t.value.count('\n')
        # token is discarded by default

    # Ignoring comments
    @_(r'#.*')
    def COMMENT(self, t):
        pass

# =================================================================
# READING THE INPUT FILE
# =================================================================
def readFile(filename):
    fn = filename
    try:
        with open(fn, "r") as f:
            script = f.read()
            return script
    except Exception as e:
        print(f"failed to read file '{fn}' : \n" + str(e))


# =================================================================
# # PRODUCE STRING OUT OF TOKENS
# =================================================================
def stringifyTokens(tokens):
    output = ''
    for tok in tokens:
        output += f'type=%r, value=%r' % (tok.type, tok.value) + '\n'
    return output