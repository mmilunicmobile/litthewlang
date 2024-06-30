from typing import Any
import lark
from enum import Enum

from typeguard import typechecked

import sys

import argparse


class PrimitiveType(Enum):
    NUM = 1
    STR = 2
    BOOL = 3

class GenderType(Enum):
    MALE = 1
    FEMALE = 2

@typechecked 
class GeneralType():
    def __init__(self, primitive_type: PrimitiveType, gender_type: GenderType):
        self.primitive_type = primitive_type
        self.gender_type = gender_type
    
    def get_primitive_type(self) -> PrimitiveType:
        return self.primitive_type
    
    def get_gender_type(self) -> GenderType:
        return self.gender_type
    
    def __repr__(self):
        return f"{self.primitive_type} {self.gender_type}"
    
    def __eq__(self, other):
        return self.primitive_type == other.primitive_type and self.gender_type == other.gender_type


argument_parser = argparse.ArgumentParser(
                    prog='Litthew Interpreter',
                    description='This will interpret your Litthewlang programs.',
                    epilog='This is version v0.2.0')

argument_parser.add_argument('filename')
argument_parser.add_argument('-t', '--no-type-check',
                    action='store_true')  # on/off flag
argument_parser.add_argument('-g', '--no-gender-check',
                    action='store_true') 
argument_parser.add_argument('-n', '--no-name-check',
                    action='store_true')

arguments = argument_parser.parse_args()

DO_SEMANTIC_NAME_CHECK = not arguments.no_gender_check
DO_TYPE_CHECK = not arguments.no_type_check
DO_GENDER_CHECK = not arguments.no_gender_check

with open('litthewlang.lark', 'r') as f:
    content = f.read()

parser = lark.Lark(content)


programName = arguments.filename

# basically this contains a dict of all global variable names and their values
variable_dict_globals = {
    "falso": False,
    "truo": True,
    "falsa": False,
    "trua": True
}

# same thing as above but stacking for function scope
variable_dict_stack = [{}]

# this is a dict of all the global variable types
variable_dict_globals_types = {
    "falso": GeneralType(PrimitiveType.BOOL, GenderType.MALE),
    "truo": GeneralType(PrimitiveType.BOOL, GenderType.MALE),
    "falsa": GeneralType(PrimitiveType.BOOL, GenderType.FEMALE),
    "trua": GeneralType(PrimitiveType.BOOL, GenderType.FEMALE)
}

# these are some lists that include all of certain created types to run type checking and stuff on them in a correct order
typechecks = []

functions_dict_globals = {}

# includes tuples of (name, [param, param, param, return type])
functions_dict_globals_types = {}
functions_dict_globals_types_params = {}

string_heap = {}
num_heap = {}
bool_heap = {}

def parse(text):
    return parser.parse(text)

class TreeToCode(lark.Transformer):
    def string(self, s):
        [string, gender] = s
        return PrimitiveExpression(string, PrimitiveType.STR, gender)
    
    def num(self, s):
        [num, gender] = s
        return PrimitiveExpression(float(num), PrimitiveType.NUM, gender)
    
    ESCAPED_STRING = lambda _, s : s[1:-1]

    MNAME = lambda _, s : s[:]

    name = lambda _, s: s[0]

    m = lambda _, n: GenderType.MALE
    f = lambda _, n: GenderType.FEMALE

    string_type = lambda _, n: PrimitiveType.STR
    num_type = lambda _, n: PrimitiveType.NUM
    boolean_type = lambda _, n: PrimitiveType.BOOL

    def expression(self, s):
        [s] = s
        if isinstance(s, PrimitiveExpression):
            return s
        elif isinstance(s, FunctionExpression):
            return s
        elif isinstance(s, str):
            return VariableExpression(s)
    
    def parameter(self, s):
        return (s[2], GeneralType(s[1], s[0]))
    
    def function_head(self, s):
        name = s[0]
        args = s[1:]
        if args == [None]:
            args = []
        return {
            'name': name,
            'parameters': dict(args)
        }
    
    def function_defo(self, s):
        return self.function_def(s, GenderType.MALE)

    def function_def(self, s, gender):
        return FunctionDefenition(s[0]["name"], s[0]["parameters"], ExecutableSequence(s[1:]), gender)
    
    def assignment(self, s):
        val = ExecutableAssignment(s[0], s[1])
        typechecks.append(val)
        return val
    
    def creation(self, s):
        val = ExecutableCreation(GeneralType(s[1], s[0]), s[2], s[3])
        typechecks.append(val)
        return val
    
    def function_call(self, s):
        name = s[0]
        args = s[1:]
        if args == [None]:
            args = []
        val = FunctionExpression(s[0], *args)
        typechecks.append(val)
        return val
    
    def program(self, s):
        return Program(s)

def to_code(tree):
    return TreeToCode().transform(tree)

#expressions have these methods
# get value (returns base python value)
# get type (returns the type of the expression) ("num" "str" "bool", "m", "f")

class Expression():
    def get_value(self):
        pass
    def get_primitive_type(self) -> PrimitiveType:
        pass
    def get_gender_type(self) -> GenderType:
        pass

    def get_type(self) -> GeneralType:
        return GeneralType(self.get_primitive_type(), self.get_gender_type())

class Executable():
    def execute(self):
        pass

@typechecked
class PrimitiveExpression(Expression):
    def __init__(self, value, primitive_type: PrimitiveType, gender_type: GenderType):
        self.value = value
        self.primitive_type = primitive_type
        self.gender_type = gender_type
    
    def get_value(self):
        return self.value
    
    def get_primitive_type(self) -> PrimitiveType:
        return self.primitive_type
    
    def get_gender_type(self) -> GenderType:
        return self.gender_type
    
    def __repr__(self):
        return f"{repr(self.value)} {self.gender_type} {self.primitive_type}"
    
    def setScope(self, scope):
        pass

@typechecked
class VariableExpression(Expression):
    def __init__(self, name: str):
        self.name = name
        self.parentScopeTypes = {}
    
    def get_value(self):
        if self.name in variable_dict_stack[-1].keys():
            return variable_dict_stack[-1][self.name]
        else:
            return variable_dict_globals[self.name]
    
    def get_primitive_type(self) -> PrimitiveType:
        if (self.name) in self.parentScopeTypes.keys():
            return self.parentScopeTypes[self.name].get_primitive_type()
        else:
            assert (self.name) in variable_dict_globals_types.keys()
            return variable_dict_globals_types[self.name].get_primitive_type()
        
    def get_gender_type(self) -> GenderType:
        if (self.name) in self.parentScopeTypes.keys():
            return self.parentScopeTypes[self.name].get_gender_type()
        else:
            assert (self.name) in variable_dict_globals_types.keys()
            return variable_dict_globals_types[self.name].get_gender_type()
        
    def setScope(self, scope):
        self.parentScopeTypes = scope

@typechecked
class FunctionExpression(Expression, Executable):
    def __init__(self, name: str, *args):
        self.name = name
        self.args = args
    
    def execute(self):
        executor = functions_dict_globals[self.name]
        executor(*self.args)
    
    def get_primitive_type(self) -> PrimitiveType:
        return functions_dict_globals_types[self.name].get_primitive_type()
    
    def get_gender_type(self) -> GenderType:
        return functions_dict_globals_types[self.name].get_gender_type()
    
    def get_value(self):
        executor = functions_dict_globals[self.name]
        return executor(*self.args)
    
    def setScope(self, scope):
        for arg in self.args:
            arg.setScope(scope)

    def typecheck(self):
        for a, b in zip(self.args, functions_dict_globals_types_params[self.name]):
            assert a.get_type() == b
    
    def __repr__(self):
        return "<" + repr(self.name) + " " + repr(self.args) + ">"

class ExecutableSequence(Executable):
    def __init__(self, expressions):
        self.expressions = expressions
    
    def execute(self):
        for expression in self.expressions:
            expression.execute()
    
    def __repr__(self):
        return "<ExecutableSequence: " + repr(self.expressions) + ">"
    
class ExecutableAssignment(Executable):
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression
    
    def execute(self):
        if self.name in variable_dict_stack[-1].keys():
            variable_dict_stack[-1][self.name] = self.expression.get_value()
        else:
            assert (self.name) in variable_dict_globals.keys() 
            variable_dict_globals[self.name] = self.expression.get_value()
    
    def __repr__(self):
        return "<ExecutableAssignment: " + repr({ "name": self.name, "expression": self.expression}) + ">"

    def setScope(self, scope):
        self.expression.setScope(scope)
        self.scope = scope

    def typecheck(self):
        my_type = self.expression.get_type()
        other_my_tpye = self.scope[self.name]
        assert my_type == other_my_tpye

class ExecutableCreation(Executable):
    def __init__(self, general_type, name, expression):
        self.general_type = general_type
        self.name = name
        self.expression = expression
    
    def execute(self):
        if self.name in variable_dict_stack[-1].keys():
            variable_dict_stack[-1][self.name] = self.expression.get_value()
        else:
            assert (self.name) in variable_dict_globals.keys()
            variable_dict_globals[self.name] = self.expression.get_value()
    
    def __repr__(self):
        return "<ExecutableCreation: " + repr({"general_type": self.general_type, "name": self.name, "expression": self.expression}) + ">"

    def setScope(self, scope):
        self.expression.setScope(scope)

    def typecheck(self):
        my_type = self.expression.get_type()
        other_my_tpye = self.general_type
        assert my_type == other_my_tpye

class FunctionDefenition():
    def __init__(self, name, params, executable_sequence, gender: GenderType):
        self.name = name
        self.executable_sequence = executable_sequence
        self.params = params
        self.scope = {}
        self.type_scope = {}
        self.gender = gender

    def executeFunction(self, *args):
        #print(f"Executing function {self.name} {args}")
        temp_scope = self.scope.copy()
        for i, value in enumerate(args):
            assert (list(self.params.keys())[i]) in temp_scope
            temp_scope[list(self.params.keys())[i]] = value.get_value()
        variable_dict_stack.append(temp_scope)
        self.executable_sequence.execute()
        output = 0.0
        if ("returno" in variable_dict_stack[-1].keys()):
            output = variable_dict_stack[-1]["returno"]
        elif ("returna" in variable_dict_stack[-1].keys()):
            output = variable_dict_stack[-1]["returna"]
        variable_dict_stack.pop()
        return output
    
    def fillVariablesScopedExecutionDefinitions(self):
        for param, type_of_param in self.params.items():
            assert(param not in self.scope.keys())
            creation_type = type_of_param.get_primitive_type()
            if creation_type == PrimitiveType.NUM:
                self.scope[param] = 0.0
            elif creation_type == PrimitiveType.STR:
                self.scope[param] = ""
            elif creation_type == PrimitiveType.BOOL:
                self.scope[param] = False
            self.type_scope[param] = type_of_param

        for statement in self.executable_sequence.expressions:
            if isinstance(statement, ExecutableCreation):
                assert(statement.name not in self.scope.keys())
                creation_type = statement.general_type.get_primitive_type()
                if creation_type == PrimitiveType.NUM:
                    self.scope[statement.name] = 0.0
                elif creation_type == PrimitiveType.STR:
                    self.scope[statement.name] = ""
                elif creation_type == PrimitiveType.BOOL:
                    self.scope[statement.name] = False
                self.type_scope[statement.name] = statement.general_type
    
    def fillOutScope(self):
        for statement in self.executable_sequence.expressions:
            statement.setScope(self.type_scope)


    def __repr__(self):
        return "<FunctionDefenition: " + repr({"name": self.name, "params": self.params, "executable_sequence": self.executable_sequence}) + ">"
    
class Program():
    def __init__(self, statements):
        self.statements = statements
    
    def fillFunctionExecutionDefinitions(self):
        for statement in self.statements:
            if isinstance(statement, FunctionDefenition):
                assert statement.name not in functions_dict_globals.keys()
                functions_dict_globals[statement.name] = statement.executeFunction
                functions_dict_globals_types_params[statement.name] = statement.params
                output = GeneralType(PrimitiveType.NUM, statement.gender)
                if ("returno" in statement.type_scope):
                    output = statement.type_scope["returno"]
                    #assert(output.get_gender_type() == statement.gender)
                elif ("returna" in statement.type_scope):
                    output = statement.type_scope["returna"]
                    #assert(output.get_gender_type() == statement.gender)
                functions_dict_globals_types[statement.name] = output
                
    
    def fillVariableExecutionDefinitions(self):
        for statement in self.statements:
            if isinstance(statement, ExecutableCreation):
                assert statement.name not in variable_dict_globals.keys()
                creation_type = statement.general_type.get_primitive_type()
                if creation_type == PrimitiveType.NUM:
                    variable_dict_globals[statement.name] = 0.0
                elif creation_type == PrimitiveType.STR:
                    variable_dict_globals[statement.name] = ""
                elif creation_type == PrimitiveType.BOOL:
                    variable_dict_globals[statement.name] = False
                variable_dict_globals_types[statement.name] = statement.general_type

    def fillVariableScopedExecutionDefinitions(self):
        for statement in self.statements:
            if isinstance(statement, FunctionDefenition):
                statement.fillVariablesScopedExecutionDefinitions()
    
    def fillVariableExpressionTypes(self):
        for statement in self.statements:
            if isinstance(statement, FunctionDefenition):
                statement.fillOutScope()
            else:
                statement.setScope(variable_dict_globals_types)
    
    def executeProgram(self):
        for statement in self.statements:
            if isinstance(statement, Executable):
                statement.execute()
    
    def typecheck(self):
        for statement in typechecks:
            statement.typecheck()

    def __repr__(self):
        return "<Program: " + repr(self.statements) + ">"

def addSimpleExecutableFunctionDefinition(name: str, evaluer: Any, params: dict):
    assert name not in functions_dict_globals.keys()
    functions_dict_globals[name] = evaluer
    functions_dict_globals_types[name] = params[-1]
    functions_dict_globals_types_params[name] = params[:-1]

with open(programName, 'r') as f:
    content = f.read()

output_program = to_code(parse(content))

#number functions
addSimpleExecutableFunctionDefinition("add", 
                                      lambda x, y: x.get_value() + y.get_value(), 
                                      [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])
addSimpleExecutableFunctionDefinition("div", lambda x, y: x.get_value() / y.get_value(),
                                      [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])
addSimpleExecutableFunctionDefinition("mul", lambda x, y: x.get_value() * y.get_value(), 
                                      [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])
addSimpleExecutableFunctionDefinition("sub", lambda x, y: x.get_value() - y.get_value(), 
                                      [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])
addSimpleExecutableFunctionDefinition("mod", lambda x, y: x.get_value() / y.get_value(), 
                                      [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])
addSimpleExecutableFunctionDefinition("numtostr", lambda x: str(x.get_value()), [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.STR, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("eqnum", lambda x, y: x.get_value() == y.get_value(), [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.BOOL, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("lt", lambda x, y: x.get_value() < y.get_value(), [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.BOOL, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("gt", lambda x, y: x.get_value() > y.get_value(), [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.BOOL, GenderType.MALE)])

#string functions
addSimpleExecutableFunctionDefinition("concat", lambda x, y: x.get_value() + y.get_value(), [GeneralType(PrimitiveType.STR, GenderType.MALE), GeneralType(PrimitiveType.STR, GenderType.MALE), GeneralType(PrimitiveType.STR, GenderType.MALE)])
def printso(x):
    print(x.get_value())
    return 0
addSimpleExecutableFunctionDefinition("print", printso, [GeneralType(PrimitiveType.STR, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("eqstr", lambda x, y: x.get_value() == y.get_value(), [GeneralType(PrimitiveType.STR, GenderType.MALE), GeneralType(PrimitiveType.STR, GenderType.MALE), GeneralType(PrimitiveType.BOOL, GenderType.MALE)])

#boolean functions
addSimpleExecutableFunctionDefinition("booltostr", lambda x: "truo" if x.get_value() else "falso", [GeneralType(PrimitiveType.BOOL, GenderType.MALE), GeneralType(PrimitiveType.STR, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("eqbool", lambda x, y: x.get_value() == y.get_value(), [GeneralType(PrimitiveType.BOOL, GenderType.MALE), GeneralType(PrimitiveType.BOOL, GenderType.MALE), GeneralType(PrimitiveType.BOOL, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("not", lambda x: not x.get_value(), [GeneralType(PrimitiveType.BOOL, GenderType.MALE), GeneralType(PrimitiveType.BOOL, GenderType.MALE)])

#if statements (this is lazy)
addSimpleExecutableFunctionDefinition("lazyif",  lambda x, y, z: y.get_value() if x.get_value() else z.get_value(), [GeneralType(PrimitiveType.BOOL, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("c", lambda x: 0.0, [GeneralType(PrimitiveType.BOOL, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])

# heaps (dictionary and string substitute)
def heapSub(heap, x, y):
    heap[x] = y
    return 0

def heapGet(heap, x):
    try:
        return heap[x]
    except (KeyError):
        print("Heap Access Error: You used a variable on the heap that doesn't exist. Womp to the womp.")
addSimpleExecutableFunctionDefinition("addnum",  lambda x, y: heapSub(num_heap, x.get_value(), y.get_value()), [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])
addSimpleExecutableFunctionDefinition("getnum",  lambda x: heapGet(num_heap,x.get_value()), [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("addstr",  lambda x, y: heapSub(string_heap, x.get_value(), y.get_value()), [GeneralType(PrimitiveType.STR, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])
addSimpleExecutableFunctionDefinition("getstr",  lambda x: heapGet(string_heap, x.get_value()), [GeneralType(PrimitiveType.STR, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])

addSimpleExecutableFunctionDefinition("addbool",  lambda x, y: heapSub(bool_heap, x.get_value(), y.get_value()), [GeneralType(PrimitiveType.BOOL, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])
addSimpleExecutableFunctionDefinition("getbool",  lambda x: heapGet(string_heap, x.get_value()), [GeneralType(PrimitiveType.BOOL, GenderType.MALE), GeneralType(PrimitiveType.NUM, GenderType.MALE)])

#typing
addSimpleExecutableFunctionDefinition("type", lambda x: str(x.get_type()), [GeneralType(PrimitiveType.NUM, GenderType.MALE), GeneralType(PrimitiveType.STR, GenderType.MALE), GeneralType(PrimitiveType.BOOL, GenderType.MALE)])

# Post-Processsing Steps:
# * Run Through Semantic Name Checking (gender) for Creations and Function Definitions ~ TYPE CHECKING
# * Ensure Gender Equality ~ TYPE CHECKING


# * Run Through Name Checking for All Variables (Check that it exists in a scope) ~ SCOPE CHECKING
# * Run Through Name Checking for All Functions (Check that it exists) ~ SCOPE CHECKING


# * Fill in Global Variable Definitions ~ CODE EXECUTION
# * Fill in Variable Types for All Global Creations (ensure name uniqueness) ~ TYPE CHECKING
output_program.fillVariableExecutionDefinitions()

# * Fill in Scoped Variable Definitions ~ CODE EXECUTION
# * Fill in Variable Types for All Scoped Function Creations and Parameters (ensure name uniqueness) ~ TYPE CHECKING
output_program.fillVariableScopedExecutionDefinitions()

# * Fill in Function Execution Definitions ~ CODE EXECUTION
# * Fill in Function Types ~ TYPE CHECKING
output_program.fillFunctionExecutionDefinitions()

# backtrack and let all variable expressions know their type
output_program.fillVariableExpressionTypes()

# * Run Type Checking on Functions, Creations, and Assignments (ensure everything is taking the right types) ~ TYPE CHECKING
if (DO_TYPE_CHECK):
    output_program.typecheck()

#print(output_program)

try:
    output_program.executeProgram()
except (RecursionError):
    print("Recursion Error: You recursed too hard. Go to jail.")
except (ZeroDivisionError):
    print("Zero Division Error: You divided by zero. Your program was sucked into a black hole.")

print("Program Complete")
# print(variable_dict_globals)
# print(num_heap)