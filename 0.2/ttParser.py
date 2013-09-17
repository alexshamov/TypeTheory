import sys

import ttCore
from ttCore import *

import ttParsingStage
from ttParsingStage import *

import ttErrors

import ply.lex as lex
import ply.yacc as yacc

class Statement(object):
    pass

class SParameter(Statement):
    def __init__(self, name, term):
        self.name = name
        self.term = term
    def execute(self):
        return TGlobalVariable(Variable(self.name, type = self.term, new = True))

class SDefinition(Statement):
    def __init__(self, name, term):
        self.name = name
        self.term = term
    def execute(self):
        return TGlobalVariable(Variable(self.name, type = self.term.type(), value = self.term, new = True))

class STypedDefinition(Statement):
    # Should we check?
    def __init__(self, name, type, term):
        self.name = name
        self.type = type
        self.term = term
    def execute(self):
        return TGlobalVariable(Variable(self.name, type = self.type, value = self.term, new = True))

class SCheck(Statement):
    def __init__(self, term):
        self.term = term
    def execute(self):
        return self.term.type().normalize()

class SEvaluate(Statement):
    def __init__(self, term):
        self.term = term
    def execute(self):
        return self.term.normalize()

class SExpression(Statement):
    def __init__(self, term):
        self.term = term
    def execute(self):
        return self.term

class SContext(Statement):
    def execute(self):
        return None # TODO: implement

class SQuit(Statement):
    def execute(self):
        sys.exit()

class SSilently(Statement):
    def __init__(self, stat):
        self.stat = stat
    def execute(self):
        self.stat.execute()
        return None

keywords = \
    (
        'type',
        'parameter', 'definition', 'check', 'evaluate', 'context', 'quit', 'silently'
    )

tokens = keywords + \
    (
        'name',
        'lparen', 'rparen', 'colon', 'colonequal', 'arrow', 'darrow',
        'lbracket', 'rbracket',
        'numeral',
        'comment'
    )

precedence = \
    (
        ('nonassoc', 'colon'),
        ('right', 'arrow', 'darrow'),
        ('left', 'application')
    )

t_lparen = r'\('
t_rparen = r'\)'
t_colon = r':'
t_colonequal = r':='
t_arrow = r'->'
t_darrow = r'=>'
t_lbracket = r'\['
t_rbracket = r'\]'
t_comment = r'\#.*'

def t_name(t):
    r'[a-zA-Z][a-zA-Z0-9]*'
    if t.value in keywords:
        t.type = t.value
    return t

def t_numeral(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = ' \t\n'

def t_error(t):
    raise ttErrors.ParsingError(t)

def p_statement_parameter(t):
    'statement : parameter binder'
    t[0] = SParameter(t[2][0], t[2][1].Translate())

def p_statement_definition(t):
    'statement : definition name colonequal expression'
    t[0] = SDefinition(t[2], t[4].Translate())

def p_statement_typed_definition(t):
    'statement : definition binder colonequal expression'
    t[0] = STypedDefinition(t[2][0], t[2][1].Translate(), t[4].Translate())

def p_statement_check(t):
    'statement : check expression'
    t[0] = SCheck(t[2].Translate())

def p_statement_evaluate(t):
    'statement : evaluate expression'
    t[0] = SEvaluate(t[2].Translate())

def p_statement_expression(t):
    'statement : expression'
    t[0] = SExpression(t[1].Translate())

def p_statement_context(t):
    'statement : context'
    t[0] = SContext()

def p_statement_quit(t):
    'statement : quit'
    t[0] = SQuit()

def p_statement_comment(t):
    'statement : comment'
    t[0] = None

def p_statement_empty(t):
    'statement :'
    t[0] = None

def p_statement_silently(t):
    'statement : silently statement'
    t[0] = SSilently(t[2])

def p_binder(t):
    'binder : name colon expression %prec colon'
    t[0] = (t[1], t[3])

def p_binder_lparen(t):
    'binder : lparen binder rparen'
    t[0] = t[2]

def p_expression_comment(t):
    'expression : expression comment'
    t[0] = t[1]

def p_expression_anon_product(t):
    'expression : expression arrow expression %prec arrow'
    t[0] = PProduct('', t[1], t[3])

def p_expression_product(t):
    'expression : binder arrow expression %prec arrow'
    t[0] = PProduct(t[1][0], t[1][1], t[3])

def p_expression_lambda(t):
    'expression : binder darrow expression %prec darrow'
    t[0] = PLambda(t[1][0], t[1][1], t[3])

# For some reason precedence doesn't work here. So we emulate it.

def p_expression_application_expression(t):
    'expression : application_expression'
    t[0] = t[1]

def p_application_expression_application(t):
    'application_expression : application_expression simple_expression %prec application'
    t[0] = PApplication(t[1], t[2])

def p_application_expression_simple_expression(t):
    'application_expression : simple_expression'
    t[0] = t[1]

def p_simple_expression_type(t):
    'simple_expression : type lbracket numeral rbracket'
    t[0] = PUniverse(t[3])

def p_simple_expression_name(t):
    'simple_expression : name'
    t[0] = PVariable(t[1])

def p_simple_expression_paren(t):
    'simple_expression : lparen expression rparen'
    t[0] = t[2]

def p_error(t):
    raise ttErrors.ParsingError(t)

lex.lex()
yacc.yacc()

def debugLex(s):
    lex.input(s)
    for tok in iter(lex.token, None):
        print(repr(tok.type), repr(tok.value))

def parse(s):
    return yacc.parse(s)
