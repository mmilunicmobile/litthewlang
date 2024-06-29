# Lithewlang
Lithewlang is in verison 0.1.0. Currently it works and can be used to do things.

Version 1.0.0 will come with fully funcitonal type checking for all stuff so you don't get type errors. There probably will be a flag to not check gender type.

Version 2.0.0 will come with time travel functionality.

### Syntactical Structures:

Creation
```
m num testo = 5m
```

Assignment
```
testo = 8m
```

Function Call
```
blorpo(testo)
```

Function Definition
```
defo neatStuff_o(m int valueo)
m int returno = multo(valueo, 2m)
fino
```

### Predefined Functions

Look in the code in [badlang](badlang.py#L344-L395).

`addnum`, `getnum` and their `str` and `bool` converses act as the only way to create lists in the programming language. See 

### Run Code

Simply run `python3 lithewlang.py [your file here]` to run a `.lithew` file.

### Installation

Just download the code and make sure that the dependencies it starts yelling at you for not having you have. Really you should only need lark and typechecked. 

Basically try this.

```
pip3 install typechecked
pip3 install lark
```