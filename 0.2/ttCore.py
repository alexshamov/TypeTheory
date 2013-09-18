import ttErrors
from ttErrors import *

globalContext = {} # to be initialized with a dict of global vars indexed by names
unsafeMode = False

def setUnsafeMode(newUnsafeMode):
    global unsafeMode
    unsafeMode = newUnsafeMode

class Variable(object):
    '''A unique global variable. Occurrences of variable terms inside expressions are irrelevant.'''
    global globalContext
    def __new__(cls, name, type = None, value = None, context = globalContext, new = False):
        '''Calling Variable(name, context) refers to an existing variable in context.
        Calling Variable(name, context, new = True) creates a new one, unless it already exists, in which case an error occurs.'''
        if new:
            if name in context:
                raise VariableExists(name)
            return super(Variable, cls).__new__(cls)
        else:
            try:
                return context[name]
            except KeyError:
                raise UnknownVariableError(name)
    def __init__(self, name, type = None, value = None, context = globalContext, new = False):
        if not new:
            return
        self.name = name
        self.type = type
        self.value = value
        context[name] = self
    def __repr__(self):
        return 'Variable(' + repr(self.name) + ', type = ' + repr(self.type) + ', value = ' + repr(self.value) + ')'

class Term(object):
    '''An abstract base class of terms.
    All concrete Terms are expected to implement:
        _identical(term) - Check for syntactic equality. This is also a default for __eq__.
        _type() - Infer the term's type.
        _normalize() - Normalize eagerly.
        _normalizeLazily() - Normalize lazily.
        _apply(sub) - apply a substitution.'''
    def __eq__(self, term):
        return self._identical(term)
    def update(self):
        if not hasattr(self, '_current'):
            self._current = self
        if self._current is not self:
            self._current = self._current.update()
        return self._current
    def type(self):
        self.update()
        if not hasattr(self, '_currentType'):
            if self._current is self:
                self._currentType = self._current._type()
            else:
                self._currentType = self._current.type()
        return self._currentType
    def normalize(self):
        self.update()
        if self._current is self:
            self._current = self._current._normalize()
        else:
            self._current = self._current.normalize()
        return self._current
    def normalizeLazily(self):
        self.update()
        if self._current is self:
            self._current = self._current._normalizeLazily()
        else:
            self._current = self._current.normalizeLazily()
        return self._current

class TGlobalVariable(Term):
    '''A global Variable term'''
    def __init__(self, var):
        self.var = var
    def __repr__(self):
        return 'TGlobalVariable(' + repr(self.var) + ')'
    def __str__(self):
        return self.var.name
    def _identical(self, term):
        return (self is term) or (isinstance(term, TGlobalVariable) and (self.var is term.var))
    def _type(self):
        return self.var.type
    def _normalize(self):
        if self.var.value != None:
            return self.var.value.normalize()
        else:
            return self
    def _normalizeLazily(self):
        if self.var.value != None:
            return self.var.value.normalizeLazily()
        else:
            return self
    def _apply(self, sub):
        return self

class TBoundVariable(Term):
    def __init__(self, name, varType, deBruijn):
        '''varType is the type within the context where the variable occurs. Thus it has to be shifted all along.'''
        self.name = name
        self.varType = varType
        self.deBruijn = deBruijn
    def __repr__(self):
        return 'TBoundVariable(' + repr(self.name) + ', ' + repr(self.varType) + ', ' + repr(self.deBruijn) + ')'
    def __str__(self):
        return self.name + '[' + str(self.deBruijn) + ']'
    def _identical(self, term):
        return (self is term) or (isinstance(term, TBoundVariable) and (self.deBruijn == term.deBruijn))
    def _type(self):
        return self.varType
    def _normalize(self):
        return self
    def _normalizeLazily(self):
        return self
    def _apply(self, sub):
#       print(self.__class__.__name__ + '._apply:')
#       print('    self: ' + str(self))
#       print('    self.type: ' + str(self.type()))
#       print('    sub: ' + str(sub))
        if sub.len >= self.deBruijn:
            if unsafeMode or ((sub * self.type()).normalize() == sub[self.deBruijn].type().normalize()):
                return sub[self.deBruijn]
            else:
                raise TypeMismatchError(sub[self.deBruijn], sub[self.deBruijn].type().normalize(), (sub * self.type()).normalize())
        else:
            return TBoundVariable(self.name, TSubstitution(self.varType, sub), self.deBruijn - sub.len + sub.shift)

class TUniverse(Term):
    def __init__(self, n):
        self.n = n
    def __repr__(self):
        return 'TUniverse(' + repr(self.n) + ')'
    def __str__(self):
        return 'type[' + str(self.n) + ']'
    def _identical(self, term):
        return (self is term) or (isinstance(term, TUniverse) and (self.n == term.n))
    def _type(self):
        return TUniverse(self.n + 1)
    def _normalize(self):
        return self
    def _normalizeLazily(self):
        return self
    def _apply(self, sub):
        return self

class TAbstraction(Term):
    '''An abstract Abstraction term.'''
    def __init__(self, name, type, term):
        self.name = name
        self.varType = type
        self.term = term
    def _identical(self, term):
        return (self is term) or (isinstance(term, self.__class__) and (self.varType == term.varType) and (self.term == term.term))
    def _normalize(self):
#       print(self.__class__.__name__ + '._normalize:')
#       print('    self: ' + str(self))
#       print('    self.type: ' + str(self.type()))
        return self.__class__(self.name, self.varType.normalize(), self.term.normalize())
    def _normalizeLazily(self):
        return self
    def _apply(self, sub):
#       print(self.__class__.__name__ + '._apply: ' + str(self) + ' | ' + str(sub))
        s = Substitution(shift = 1) * sub
#       s.subs.append(TBoundVariable(self.name, s * self.varType, 1))
        s = SConcat(s, TBoundVariable(self.name, TSubstitution(self.varType, s), 1))
#       s = Substitution(shift = s.shift, subs = s.subs + [TBoundVariable(self.name, TSubstitution(self.varType, s), 1)])
        # It's dangerous to modify the data inside s here
        return self.__class__(self.name, TSubstitution(self.varType, sub), TSubstitution(self.term, s))

class TProduct(TAbstraction):
    def __init__(self, name, type, term):
        super(TProduct, self).__init__(name, type, term)
    def __repr__(self):
        return 'TProduct(' + repr(self.name) + ', ' + repr(self.varType) + ', ' + repr(self.term) + ')'
    def __str__(self):
        if self.name != '':
            return '((' + self.name + ' : ' + str(self.varType) + ') -> ' + str(self.term) + ')'
        else:
            return '(' + str(self.varType) + ' -> ' + str(self.term) + ')'
    def _type(self):
        t1 = self.varType.type().normalize()
        if not isinstance(t1, TUniverse):
            raise TypeExpectedError(self.varType)
        t2 = self.term.type().normalize()
        if not isinstance(t2, TUniverse):
            raise TypeExpectedError(self.term)
        return TUniverse(max(t1.n, t2.n))

class TLambda(TAbstraction):
    def __init__(self, name, type, term):
        super(TLambda, self).__init__(name, type, term)
    def __repr__(self):
        return 'TLambda(' + repr(self.name) + ', ' + repr(self.varType) + ', ' + repr(self.term) + ')'
    def __str__(self):
        if self.name != '':
            return '(' + self.name + ' : ' + str(self.varType) + ' => ' + str(self.term) + ')'
        else:
            return '(' + str(self.varType) + ' => ' + str(self.term) + ')'
    def _type(self):
        return TProduct(self.name, self.varType, self.term.type())

class TApplication(Term):
    def __init__(self, term1, term2):
        self.term1 = term1
        self.term2 = term2
    def __repr__(self):
        return 'TApplication(' + repr(self.term1) + ', ' + repr(self.term2) + ')'
    def __str__(self):
        return '(' + str(self.term1) + ' ' + str(self.term2) + ')'
    def _identical(self, term):
        return (self is term) or (isinstance(term, TApplication) and (self.term1 == term.term1) and (self.term2 == term.term2))
    def _type(self):
        t = self.term1.type().normalizeLazily()
        if not isinstance(t, TProduct):
            raise ProductExpectedError(self.term1)
        return TSubstitution(t.term, Substitution(subs = [self.term2]))
    def _normalize(self):
        t = self.term1.normalizeLazily()
        if isinstance(t, TLambda):
            return TSubstitution(t.normalize().term, Substitution(subs = [self.term2.normalize()])).normalize()
        else:
            return TApplication(t.normalize(), self.term2.normalize())
    def _normalizeLazily(self):
        t = self.term1.normalizeLazily()
        if isinstance(t, TLambda):
            return TSubstitution(t.term, Substitution(subs = [self.term2])).normalizeLazily()
        else:
            return TApplication(t, self.term2)
    def _apply(self, sub):
        return TApplication(sub * self.term1, sub * self.term2)

class Substitution(object):
    def __init__(self, subs = [], shift = 0):
        '''subs is a list of substitutions for de Bruijn variables. Var i is substituted for subs[i - 1], the remaining indices are shifted.'''
        self._subs = subs
        self.len = len(subs)
        self.shift = shift
    def __repr__(self):
        return 'Substitution(subs = ' + repr(self._subs) + ', shift = ' + repr(self.shift) + ')'
    def __str__(self):
        r = ''
        for s in range(self.len):
            r = r + ', ' + str(self[s + 1])
        r = r + ', shift ' + str(self.shift)
        return r[2:]
    def __getitem__(self, key):
        return self._subs[key - 1]
    def __mul__(self, other):
        if isinstance(other, Substitution):
            return SComposition(self, other)
#            if other.shift < len(self.subs):
#                return Substitution(subs = self.subs[: len(self.subs) - other.shift] + [TSubstitution(t, self) for t in other.subs], shift = self.shift)
#            else:
#                return Substitution([TSubstitution(t, self) for t in other.subs], shift = self.shift + other.shift - len(self.subs))
        elif isinstance(other, Term):
            return other._apply(self)
        else:
            return NotImplemented
    def __eq__(self, sub):
        return (self is sub) or ((self.__class__ is Substitution) and (sub.__class__ is Substitution) and (self.shift == sub.shift) and (self.len == sub.len) and
            all(self[i] == t2 for t1, t2 in zip(self._subs, sub._subs)))
    def normalize(self):
        return SNormalized(self)

class SComposition(Substitution):
    def __init__(self, sub1, sub2):
        self.sub1 = sub1
        self.sub2 = sub2
        if self.sub2.shift < self.sub1.len:
            self.shift = self.sub1.shift
            self.len = self.sub1.len - self.sub2.shift + self.sub2.len
        else:
            self.shift = self.sub1.shift + self.sub2.shift - self.sub1.len
            self.len = self.sub2.len
        self._lazySubs = {}
        for i in range(self.len):
            self[i + 1]
    def __getitem__(self, key):
        try:
            return self._lazySubs[key]
        except KeyError:
            if (self.sub2.shift >= self.sub1.len) or (key <= self.sub2.len):
                r = TSubstitution(self.sub2[key], self.sub1)
            else:
                r = self.sub1[key + self.sub2.shift - self.sub2.len]
            self._lazySubs[key] = r
            return r

class SConcat(Substitution):
    def __init__(self, sub, term):
        self.sub = sub
        self.term = term
        self.shift = sub.shift
        self.len = sub.len + 1
        for i in range(self.len):
            self[i + 1]
    def __getitem__(self, key):
        if key == 1:
            return self.term
        else:
            return self.sub[key - 1]

class SNormalized(Substitution):
    def __init__(self, sub):
        self.sub = sub
        self.shift = sub.shift
        self.len = sub.len
    def __getitem__(self, key):
        return self.sub[key].normalize()
    def normalize(self):
        return self

class TSubstitution(Term):
    def __init__(self, term, sub):
        self.term = term
        self.sub = sub
    def __repr__(self):
        return 'TSubstitution(' + repr(self.term) + ', ' + repr(self.sub) + ')'
    def __str__(self):
        return '(' + str(self.term) + ' | ' + str(self.sub) + ')'
    def _identical(self, term):
        return (self is term) or (isinstance(term, TSubstitution) and (self.term == term.term) and (self.sub == term.sub))
    def _type(self):
        return TSubstitution(self.term.type(), self.sub)
    def _normalize(self):
#       print(self.__class__.__name__ + '._normalize:')
#       print('    self: ' + str(self))
#       print('    self.type: ' + str(self.type()))
        return (self.sub.normalize() * self.term.normalize()).normalize()
    def _normalizeLazily(self):
        return (self.sub * self.term).normalizeLazily()
    def _apply(self, sub):
        return TSubstitution(self.term, sub * self.sub)

