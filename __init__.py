import ttCore
from ttCore import *

import ttParser
from ttParser import *

import ttErrors

import readline

import sys

sys.setrecursionlimit(10000)

def printContext(context, header = 'Context:'):
    print(header)
    for ((name, sub), (type, expr)) in context.items():
        print('    ' + name + '[' + str(sub) + '] : ' + str(type) + ' = ' + str(expr))

def printUsedVars():
    print('UsedVars:')
    for (name,  val) in usedVars.items():
        print('    ' + name + ' = ' + str(val))

if len(sys.argv) == 2:
    for s in open(sys.argv[1]):
        r = parse(s)
        if r != None:
            print(r.execute())

while True:
    s = input('> ')
    try:
        r = parse(s)
        print(r.execute())
    except (ttErrors.ParsingError, ttErrors.TypeTheoreticError) as e:
        print(e)
        printContext(e.context)
        printContext(globalContext, 'Global context:')
        printUsedVars()
