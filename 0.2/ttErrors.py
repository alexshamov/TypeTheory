class TypeTheoreticError(Exception):
    pass

class UnknownVariableError(TypeTheoreticError):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return 'Unknown variable: ' + self.name

class VariableExists(TypeTheoreticError):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return 'Variable exists: ' + self.name

class TypeExpectedError(TypeTheoreticError):
    def __init__(self, term):
        self.term = term
    def __str__(self):
        return 'Type expected: ' + str(self.term)

class ProductExpectedError(TypeTheoreticError):
    def __init__(self, term):
        self.term = term
    def __str__(self):
        return 'Product expected: ' + str(self.term)

class TypeMismatchError(TypeTheoreticError):
    def __init__(self, term, type, expectedType):
        self.term = term
        self.type = type
        self.expectedType = expectedType
    def __str__(self):
        return 'Type mismatch: ' + str(self.term) + ' : ' + str(self.type) + ', expected ' + str(self.expectedType)

class RecursionError(TypeTheoreticError):
    def __init__(self, term):
        self.term = term
    def __str__(self):
        return 'Recursion error: ' + str(self.term)

class ParsingError(Exception):
    def __init__(self, token):
        self.token = token
    def __str__(self):
        return 'Parsing error at token ' + self.token.type
