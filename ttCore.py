import ttErrors

usedVars = {'': 0}
globalContext = {}

class Variable(object):
    def __init__(self, name = '', sub = None):
# None means that we introduce a unique variable; otherwise we refer to an existing one
        global usedVars
        if sub == None:
            try:
                sub = usedVars[name]
            except KeyError:
                sub = 0
                usedVars[name] = 0
        self.name = name
        self.sub = sub
        self.namesub = (self.name, self.sub)
        try:
            usedVars[name] = max(usedVars[name], sub + 1)
        except KeyError:
            usedVars[name] = sub + 1
    def __repr__(self):
        return 'Variable(' + repr(self.name) + ', ' + repr(self.sub) + ')'

class Abstraction(object):
    def __init__(self, var, type, expr):
        self.var = var
        self.type = type
        self.expr = expr
    def __repr__(self):
        return 'Abstraction(' + repr(self.var) + ', ' + repr(self.type) + ', ' + repr(self.expr) + ')'
    def subst(self, dict):
        return Abstraction(self.var, self.type.subst(dict), self.expr.subst(dict))
    def identical(self, abs):
        if self.type.identical(abs.type):
            v = Variable()
            t1 = self.expr.subst({self.var.namesub: TVariable(v)})
            t2 = abs.expr.subst({abs.var.namesub: TVariable(v)})
            return t1.identical(t2)
        else:
            return False
    def normalize(self, context):
        newvar = Variable(self.var.name)
        newtype = self.type.subst({self.var.namesub: TVariable(newvar)}).normalize(context)
        newcontext = context.copy()
        newcontext[newvar.namesub] = (newtype, None)
        return Abstraction(newvar, newtype, self.expr.subst({self.var.namesub: TVariable(newvar)}).normalize(newcontext))

class Term(object):
    def __init__(self):
        raise ttErrors.AbstractError()
    def __repr__(self):
        return 'Term()'
    def subst(self, dict):
        raise ttErrors.AbstractError()
    def identical(self, term):
        raise ttErrors.AbstractError()
    def inferType(self, context):
        raise ttErrors.AbstractError()
    def normalize(self, context):
        raise ttErrors.AbstractError()
    def equal(self, term, context):
        return self.normalize(context).identical(term.normalize(context))
    def inferUniverse(self, context):
        u = self.inferType(context).normalize(context)
        if isinstance(u, TUniverse):
            return u.n
        else:
            raise ttErrors.TypeExpectedError(self, context)
    def inferProduct(self, context):
        p = self.inferType(context).normalize(context)
        if isinstance(p, TProduct):
            return p.abs
        else:
            raise ttErrors.ProductExpectedError(self, context)

class TVariable(Term):
    def __init__(self, var):
        self.var = var # Variable
    def __repr__(self):
        return 'TVariable(' + repr(self.var) + ')'
    def __str__(self):
        if self.var.sub == 0:
            return self.var.name
        else:
            return self.var.name + '[' + str(self.var.sub) + ']'
    def subst(self, dict):
        try:
            return dict[self.var.namesub]
        except KeyError:
            return self
    def identical(self, term):
        return (self == term) or (isinstance(term, TVariable) and (self.var.namesub == term.var.namesub))
    def inferType(self, context):
        try:
            return context[self.var.namesub][0]
        except KeyError:
            raise ttErrors.UnknownVariableError(self.var, context)
    def normalize(self, context):
        try:
            return context[self.var.namesub][1].normalize(context)
        except (KeyError, AttributeError):
            return self
        except RuntimeError:
            raise ttErrors.RecursionError(self,  context)

class TUniverse(Term):
    def __init__(self, n):
        self.n = n # int
    def __repr__(self):
        return 'TUniverse(' + repr(self.n) + ')'
    def __str__(self):
        return 'type[' + str(self.n) + ']'
    def subst(self, dict):
        return self
    def identical(self, term):
        return (self == term) or (isinstance(term, TUniverse) and (self.n == term.n))
    def inferType(self, context):
        return TUniverse(self.n + 1)
    def normalize(self, context):
        return self

class TProduct(Term):
    def __init__(self, abs):
        self.abs = abs # Abstraction
    def __repr__(self):
        return 'TProduct(' + repr(self.abs) + ')'
    def __str__(self):
        return '((' + str(TVariable(self.abs.var)) + ' : ' + str(self.abs.type) + ') -> ' + str(self.abs.expr) + ')'
    def subst(self, dict):
        return TProduct(self.abs.subst(dict))
    def identical(self, term):
        return (self == term) or (isinstance(term, TProduct) and self.abs.identical(term.abs))
    def inferType(self, context):
        n1 = self.abs.type.inferUniverse(context)
        newcontext = context.copy()
        newcontext[self.abs.var.namesub] = (self.abs.type, None)
        n2 = self.abs.expr.inferUniverse(newcontext)
        return TUniverse(max(n1, n2))
    def normalize(self, context):
        return TProduct(self.abs.normalize(context))

class TLambda(Term):
    def __init__(self, abs):
        self.abs = abs # Abstraction
    def __repr__(self):
        return 'TLambda(' + repr(self.abs) + ')'
    def __str__(self):
        return '((' + str(TVariable(self.abs.var)) + ' : ' + str(self.abs.type) + ') => ' + str(self.abs.expr) + ')'
    def subst(self, dict):
        return TLambda(self.abs.subst(dict))
    def identical(self, term):
        return (self == term) or (isinstance(term, TLambda) and self.abs.identical(term.abs))
    def inferType(self, context):
        self.abs.type.inferUniverse(context)
        newcontext = context.copy()
        newcontext[self.abs.var.namesub] = (self.abs.type, None)
        return TProduct(Abstraction(self.abs.var, self.abs.type, self.abs.expr.inferType(newcontext)))
    def normalize(self, context):
        return TLambda(self.abs.normalize(context))

class TApplication(Term):
    def __init__(self, term1, term2):
        self.term1 = term1
        self.term2 = term2
    def __repr__(self):
        return 'TApplication(' + repr(self.term1) + ', ' + repr(self.term2) + ')'
    def __str__(self):
        return '(' + str(self.term1) + ' ' + str(self.term2) + ')'
    def subst(self, dict):
        return TApplication(self.term1.subst(dict), self.term2.subst(dict))
    def identical(self, term):
        return (self == term) or (isinstance(term, TApplication) and self.term1.identical(term.term1) and self.term2.identical(term.term2))
    def inferType(self, context):
        p = self.term1.inferProduct(context)
        if p.type.equal(self.term2.inferType(context), context):
            return p.expr.subst({p.var.namesub: self.term2})
        else:
            raise ttErrors.TypeMismatchError(self, context)
    def normalize(self, context):
        p = self.term1.inferProduct(context)
        if p.type.equal(self.term2.inferType(context), context):
            t1 = self.term1.normalize(context)
            t2 = self.term2.normalize(context)
            if isinstance(t1, TLambda):
                newcontext = context.copy()
                newcontext[t1.abs.var.namesub] = (t2.inferType(context), t2)
                return t1.abs.expr.normalize(newcontext)
            else:
                return TApplication(t1, t2)
        else:
            raise ttErrors.TypeMismatchError(self, context)
