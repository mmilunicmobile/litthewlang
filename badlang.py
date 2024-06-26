from typing import Any
import lark
from enum import Enum

from typeguard import typechecked

with open('badlang.lark', 'r') as f:
    content = f.read()

parser = lark.Lark(content)

# basically this contains a dict of all global variable names and their values
variable_dict_globals = {}

# same thing as above but stacking for function scope
variable_dict_stack = [{}]

# this is a dict of all the global variable types
variable_dict_globals_types = {}

# these are some lists that include all of certain created types to run type checking and stuff on them in a correct order
variable_expression_list = []

functions_dict_globals = {}

# includes tuples of (name, [param, param, param, return type])
functions_dict_globals_types = {}


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
        return self.function_def(s)

    def function_def(self, s):
        return FunctionDefenition(s[0]["name"], s[0]["parameters"], ExecutableSequence(s[1:]))
    
    def assignment(self, s):
        return ExecutableAssignment(s[0], s[1])
    
    def creation(self, s):
        return ExecutableCreation(GeneralType(s[1], s[0]), s[2], s[3])
    
    def function_call(self, s):
        name = s[0]
        args = s[1:]
        if args == [None]:
            args = []
        return FunctionExpression(s[0], *args)
    
    def program(self, s):
        return Program(s)

def to_code(tree):
    return TreeToCode().transform(tree)

#expressions have these methods
# get value (returns base python value)
# get type (returns the type of the expression) ("num" "str" "bool", "m", "f")


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

class Expression():
    def get_value(self):
        pass
    def get_primitive_type(self) -> PrimitiveType:
        pass
    def get_gender_type(self) -> GenderType:
        pass

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
        if self.name in self.parentScopeTypes.keys():
            return self.parentScopeTypes[self.name].get_primitive_type()
        
    def get_gender_type(self) -> GenderType:
        if self.name in self.parentScopeTypes.keys():
            return self.parentScopeTypes[self.name].get_gender_type()

@typechecked
class FunctionExpression(Expression, Executable):
    def __init__(self, name: str, *args):
        self.name = name
        self.args = args
    
    def get_value(self):
        executor = functions_dict_globals[self.name]
        return executor(self.args)
    
    def get_primitive_type(self) -> PrimitiveType:
        return functions_dict_globals_types[self.name][-1].get_primitive_type()
    
    def get_gender_type(self) -> GenderType:
        return functions_dict_globals_types[self.name][-1].get_gender_type()
    
    def execute(self):
        return self.get_value()
    
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

class FunctionDefenition():
    def __init__(self, name, params, executable_sequence):
        self.name = name
        self.executable_sequence = executable_sequence
        self.params = params
        self.scope = params

    def executeFunction(self, *args):
        print(f"Executing function {self.name}")
        variable_dict_stack.append(self.scope.copy())
        for i, value in enumerate(args):
            assert (list(self.params.keys())[i]) in variable_dict_stack[-1]
            variable_dict_stack[-1][self.params.keys()[i]] = value
        self.executable_sequence.execute()
        variable_dict_stack.pop()

    def __repr__(self):
        return "<FunctionDefenition: " + repr({"name": self.name, "params": self.params, "executable_sequence": self.executable_sequence}) + ">"
    
class Program():
    def __init__(self, statements):
        self.statements = statements
    
    def fillFunctionExecutionDefinitions(self):
        for statement in self.statements:
            if isinstance(statement, FunctionDefenition):
                functions_dict_globals[statement.name] = statement.executeFunction
    
    def fillVariableExecutionDefinitions(self):
        for statement in self.statements:
            if isinstance(statement, ExecutableCreation):
                creation_type = statement.general_type.get_primitive_type()
                if creation_type == PrimitiveType.NUM:
                    variable_dict_globals[statement.name] = 0
                elif creation_type == PrimitiveType.STR:
                    variable_dict_globals[statement.name] = ""
                elif creation_type == PrimitiveType.BOOL:
                    variable_dict_globals[statement.name] = False

    def fillVariableScopedExecutionDefinitions(self):
        for statement in self.statements:
            if isinstance(statement, FunctionDefenition):
                statement.fillVariablesScopedExecutionDefinitions()
    
    def executeProgram(self):
        for statement in self.statements:
            if isinstance(statement, Executable):
                statement.execute()

    def __repr__(self):
        return "<Program: " + repr(self.statements) + ">"

with open('test.lithew', 'r') as f:
    content = f.read()

output_program = to_code(parse(content))

# Post-Processsing Steps:
# * Fill in Variable Types for All Global Creations (ensure name uniqueness) ~ TYPE CHECKING
# * Fill in Variable Types for All Scoped Function Creations and Parameters (ensure name uniqueness) ~ TYPE CHECKING
# * Fill in Function Types ~ TYPE CHECKING
# * Run Through Semantic Name Checking (gender) for Creations and Function Definitions ~ TYPE CHECKING
# * Ensure Gender Equality ~ TYPE CHECKING
# * Run Through Name Checking for All Variables (Check that it exists in a scope) ~ SCOPE CHECKING
# * Run Through Name Checking for All Functions (Check that it exists) ~ SCOPE CHECKING
# * Run Type Checking on Functions, Creations, and Assignments (ensure everything is taking the right types) ~ TYPE CHECKING
# * Fill in Function Execution Definitions ~ CODE EXECUTION
output_program.fillFunctionExecutionDefinitions()
# * Fill in Global Variable Definitions ~ CODE EXECUTION
output_program.fillVariableExecutionDefinitions()
# * Fill in Scoped Variable Definitions ~ CODE EXECUTION

print(output_program)

output_program.executeProgram()

print(variable_dict_globals)