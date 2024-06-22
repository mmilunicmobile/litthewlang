from typing import Any
import lark
from enum import Enum

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
        elif isinstance(s, str):
            return VariableExpression(s)

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

class GeneralType():
    def __init__(self, primitive_type: PrimitiveType, gender_type: GenderType):
        self.primitive_type = primitive_type
        self.gender_type = gender_type
    
    def get_primitive_type(self):
        return self.primitive_type
    
    def get_gender_type(self):
        return self.gender_type

class PrimitiveExpression():
    def __init__(self, value, primitive_type: PrimitiveType, gender_type: GenderType):
        self.value = value
        self.primitive_type = primitive_type
        self.gender_type = gender_type
    
    def get_value(self):
        return self.value
    
    def get_primitive_type(self):
        return self.primitive_type
    
    def get_gender_type(self):
        return self.gender_type

class VariableExpression():
    def __init__(self, name):
        self.name = name
        self.parentScopeTypes = {}
    
    def get_value(self):
        if self.name in variable_dict_stack[-1].keys():
            return variable_dict_stack[-1][self.name]
        else:
            return variable_dict_globals[self.name]
    
    def get_primitive_type(self):
        if self.name in self.parentScopeTypes.keys():
            return self.parentScopeTypes[self.name].get_primitive_type()
        
    
    def get_gender_type(self):
        if self.name in self.parentScopeTypes.keys():
            return self.parentScopeTypes[self.name].get_gender_type()

class FunctionExpression():
    def __init__(self, name, *args):
        self.name = name
        self.args = args
    
    def get_value(self):
        return functions_dict_globals[self.name].execute(self.args)
    
    def get_primitive_type(self):
        return functions_dict_globals_types[self.name][-1].get_primitive_type()
    
    def get_gender_type(self):
        return functions_dict_globals_types[self.name][-1].get_gender_type()
    
class ExecutableSequence():
    def __init__(self, expressions):
        self.expressions = expressions
    
    def execute(self):
        for expression in self.expressions:
            expression.execute()

with open('test.lithew', 'r') as f:
    content = f.read()
    print(repr(to_code(parse(content))))

# Post-Processsing Steps:
# * Fill in Variable Types for All Global Creations (ensure name uniqueness)
# * Fill in Variable Types for All Scoped Function Creations and Parameters (ensure name uniqueness)
# * Fill in Function Types
# * Run Through Semantic Name Checking (gender) for Creations and Function Definitions
# * Ensure Gender Equality
# * Run Through Name Checking for All Variables (Check that it exists in a scope)
# * Run Through Name Checking for All Functions (Check that it exists)
# * Run Type Checking on Functions, Creations, and Assignments (ensure everything is taking the right types)