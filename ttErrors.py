class TypeTheoreticError(Exception):
    pass

class AbstractError(TypeTheoreticError):
    def __str__(self):
        return 'Abstract call'

class UnknownVariableError(TypeTheoreticError):
    def __init__(self, var, context):
        self.var = var
        self.context = context
    def __str__(self):
        return 'Unknown variable: ' + str(self.var.namesub)

class TypeExpectedError(TypeTheoreticError):
    def __init__(self, expr, context):
        self.expr = expr
        self.context = context
    def __str__(self):
        return 'Type expected: ' + str(self.expr)

class ProductExpectedError(TypeTheoreticError):
    def __init__(self, expr, context):
        self.expr = expr
        self.context = context
    def __str__(self):
        return 'Product expected: ' + str(self.expr)

class TypeMismatchError(TypeTheoreticError):
    def __init__(self, expr, context):
        self.expr = expr
        self.context = context
    def __str__(self):
        return 'Type mismatch: ' + str(self.expr)

class RecursionError(TypeTheoreticError):
    def __init__(self, expr, context):
        self.expr = expr
        self.context = context
    def __str__(self):
        return 'Recursion error: ' + str(self.expr)

class ParsingError(Exception):
    def __str__(self):
        return 'Parsing error'
