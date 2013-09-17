import ttCore
from ttCore import *

# A separate simplified class hierarchy designed for handling named variables and turning them into de Bruijn indices

class PTerm(object):
    def mergeFree(self):
        for c in self.children:
            for name in c.free:
                if name in self.free:
                    self.free[name] = self.free[name] + c.free[name]
                else:
                    self.free[name] = c.free[name]
    def raiseIndices(self):
        for name in self.free:
            for var in self.free[name]:
                var.deBruijn = var.deBruijn + 1
    def calcIndices(self):
        for c in self.children:
            c.calcIndices()
    def inferTypes(self):
        for c in self.children:
            c.inferTypes()
    def Translate(self):
        for name in self.free:
            for var in self.free[name]:
                var.glob = True
        self.calcIndices()
        self.inferTypes()
        return self.translate()

class PVariable(PTerm):
    def __init__(self, name):
        self.name = name
        self.type = None
        self.free = {name: [self]}
        self.children = []
        self.deBruijn = 0
        self.glob = False
    def translate(self):
        if self.glob:
            return TGlobalVariable(Variable(self.name))
        else:
            return TBoundVariable(self.name, self.type.translate(), self.deBruijn)

class PBinder(PTerm):
    def __init__(self, name, term):
        self.name = name
        self.term = term
        self.children = [term]
        self.free = {}
        self.mergeFree()
    def mergeFree(self):
        for name in self.term.free:
            if name != self.name:
                if name in self.free:
                    self.free[name] = self.free[name] + self.term.free[name]
                else:
                    self.free[name] = self.term.free[name]
    def calcIndices(self):
        self.term.raiseIndices()
        super().calcIndices()
    def translate(self):
        return self.term.translate()

class PAbstraction(PTerm):
    def __init__(self, name, type, term):
        self.name = name
        self.type = type
        self.term = term
        self.children = [type, PBinder(name, term)]
        self.free = {}
        self.mergeFree()
    def inferTypes(self):
        if self.name in self.term.free:
            for v in self.term.free[self.name]:
                v.type = self.type
        super().inferTypes()

class PUniverse(PTerm):
    def __init__(self, n):
        self.n = n
        self.children = []
        self.free = {}
    def translate(self):
        return TUniverse(self.n)

class PProduct(PAbstraction):
    def __init__(self, name, type, term):
        super().__init__(name, type, term)
    def translate(self):
        return TProduct(self.name, self.type.translate(), self.term.translate())

class PLambda(PAbstraction):
    def __init__(self, name, type, term):
        super().__init__(name, type, term)
    def translate(self):
        return TLambda(self.name, self.type.translate(), self.term.translate())

class PApplication(PTerm):
    def __init__(self, term1, term2):
        self.term1 = term1
        self.term2 = term2
        self.children = [term1, term2]
        self.free = {}
        self.mergeFree()
    def translate(self):
        return TApplication(self.term1.translate(), self.term2.translate())
