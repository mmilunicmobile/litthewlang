# litthewlang
litthewlang is in verison 0.1.0. Currently it works and can be used to do things.

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

Look in the code in [badlang](litthewlang.py#L508-L571).

`addnum`, `getnum` and their `str` and `bool` converses act as the only way to create lists in the programming language.

`type`, `c`, and `meta` take any type and have no typechecking applied to their arguments. They are also lazy and do not evaluate their arguments.

`lazyif` does not evaluate its argument unless it absolutely has to. This can be used to create branching code.

### Run Code

Simply run `python3 litthewlang.py [your file here]` to run a file.

Officially the perferred ending to a file is `.litthew` for now.

### Flags
Use the flag `-t` to remove typechecking.

### Installation

Just download the code and make sure that the dependencies it starts yelling at you for not having you have. Really you should only need lark and typechecked. 

Basically try this.

```
pip3 install typechecked
pip3 install lark
```
