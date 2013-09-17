import ttCore
from ttCore import *

import ttParser
from ttParser import *

import ttErrors

import readline

import sys

sys.setrecursionlimit(1000000)

def printContext(context, header = 'Context:'):
    print(header)
    for (name, var) in context.items():
        print('    ' + name + ' : ' + str(var.type) + ' = ' + str(var.value))

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
        printContext(globalContext, 'Global context:')
