from typing import Any
import lark
from enum import Enum

with open('badlang.lark', 'r') as f:
    content = f.read()

parser = lark.Lark(content)

variable_dict = {}

def parse(text):
    return parser.parse(text)

class TreeToCode(lark.Transformer):
    def string(self, s):
        [string, gender] = s
        return PrimitiveExpression(string, PrimitiveTypes.STR, gender)
    
    def num(self, s):
        [num, gender] = s
        return PrimitiveExpression(float(num), PrimitiveTypes.NUM, gender)
    
    ESCAPED_STRING = lambda _, s : s[1:-1]

    MNAME = lambda _, s : s[:]

    name = lambda _, s: s[0]

    m = lambda _, n: GenderTypes.MALE
    f = lambda _, n: GenderTypes.FEMALE

    string_type = lambda _, n: PrimitiveTypes.STR
    num_type = lambda _, n: PrimitiveTypes.NUM
    boolean_type = lambda _, n: PrimitiveTypes.BOOL

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


class PrimitiveTypes(Enum):
    NUM = 1
    STR = 2
    BOOL = 3

class GenderTypes(Enum):
    MALE = 1
    FEMALE = 2

class PrimitiveExpression():
    def __init__(self, value, primitive_type: PrimitiveTypes, gender_type: GenderTypes):
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
    
    def get_value(self):
        return variable_dict[self.name][0].get_value()
    
    def get_primitive_type(self):
        return variable_dict[self.name][1]
    
    def get_gender_type(self):
        return variable_dict[self.name][2]

class FunctionExpression():
    def __init__(self, name):
        self.name = name
    
    def get_value(self):
        return variable_dict[self.name][0].execute()
    
class ExecutableSequence():
    def __init__(self, expressions):
        self.expressions = expressions
    
    def execute(self):
        for expression in self.expressions:
            expression.execute()

with open('test.lithew', 'r') as f:
    content = f.read()
    print(repr(to_code(parse(content))))