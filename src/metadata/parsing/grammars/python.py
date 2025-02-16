"""
Language-specific grammars for code parsing.
"""

# Python grammar definition
PYTHON_GRAMMAR = r"""
    // Top level file structure
    file_input: (_NEWLINE | stmt)*
    
    ?stmt: simple_stmt | compound_stmt
    ?simple_stmt: small_stmt (";" small_stmt)* [";"] _NEWLINE
    ?small_stmt: expr_stmt | import_stmt | pass_stmt | return_stmt | raise_stmt
    
    // Expression statements
    ?expr_stmt: testlist_star_expr (annassign | augassign testlist | ("=" testlist_star_expr)*)
    ?testlist_star_expr: (test|star_expr) ("," (test|star_expr))* [","]
    ?testlist: test ("," test)* [","]
    ?annassign: ":" test ["=" test]
    ?augassign: "+=" | "-=" | "*=" | "@=" | "/=" | "%=" | "&=" | "|=" | "^=" | "<<=" | ">>=" | "**=" | "//="
    
    // Import statements
    ?import_stmt: import_name | import_from
    import_name: "import" dotted_as_names
    import_from: "from" [relative_import] dotted_name "import" import_targets
                | "from" relative_import "import" import_targets  // from . import x
    relative_import: "."+ [dotted_name]
    import_targets: "*" | "(" import_as_names ")" | import_as_names
    import_as_names: import_as_name ("," import_as_name)* [","]
    ?import_as_name: NAME ["as" NAME]
    dotted_as_names: dotted_as_name ("," dotted_as_name)* [","]
    ?dotted_as_name: dotted_name ["as" NAME]
    dotted_name: NAME ("." NAME)*
    
    // Function and class definitions
    ?compound_stmt: function_def | class_def
    
    // Function definition
    ?function_def: [decorators] ["async"] "def" NAME "(" [parameters] ")" ["->" test] ":" suite
    parameters: param ("," param)* [","]
    ?param: NAME [":" test] ["=" test]
    decorators: decorator+
    decorator: "@" dotted_name ["(" [arguments] ")"] _NEWLINE
    arguments: argument ("," argument)* [","]
    ?argument: test ["=" test]
    
    // Class definition
    ?class_def: [decorators] "class" NAME ["(" [arguments] ")"] ":" suite
    
    // Basic statements
    pass_stmt: "pass"
    return_stmt: "return" [testlist]
    raise_stmt: "raise" [test ["from" test]]
    
    // Test expressions
    ?test: or_test ["if" or_test "else" test] | lambdef
    ?or_test: and_test ("or" and_test)*
    ?and_test: not_test ("and" not_test)*
    ?not_test: "not" not_test | comparison
    ?comparison: expr (comp_op expr)*
    ?comp_op: "<" | ">" | "==" | ">=" | "<=" | "!=" | "in" | "not" "in" | "is" | "is" "not"
    
    // Basic expressions
    ?expr: xor_expr ("|" xor_expr)*
    ?xor_expr: and_expr ("^" and_expr)*
    ?and_expr: shift_expr ("&" shift_expr)*
    ?shift_expr: arith_expr (("<<" | ">>") arith_expr)*
    ?arith_expr: term (("+"|"-") term)*
    ?term: factor (("*"|"@"|"/"|"%"|"//") factor)*
    ?factor: ("+"|"-"|"~") factor | power
    ?power: atom_expr ["**" factor]
    ?atom_expr: [AWAIT] atom trailer*
    
    // Atoms (basic elements)
    ?atom: "(" [testlist_comp] ")" -> tuple
         | "[" [testlist_comp] "]" -> list
         | "{" [dictorsetmaker] "}" -> dict
         | NAME -> var
         | NUMBER
         | string+
         | "..." -> ellipsis
         | "None" -> const_none
         | "True" -> const_true
         | "False" -> const_false
    
    ?testlist_comp: (test|star_expr) (comp_for | ("," (test|star_expr))* [","])
    ?trailer: "(" [arguments] ")" | "[" subscriptlist "]" | "." NAME
    ?subscriptlist: subscript ("," subscript)* [","]
    ?subscript: test | [test] ":" [test] [sliceop]
    ?sliceop: ":" [test]
    ?lambdef: "lambda" [parameters] ":" test
    
    // F-strings
    ?string: STRING | FSTRING
    FSTRING: "f" _STRING
    STRING: _STRING
    _STRING: /[ubf]?r?("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/i
    
    // Compound statements
    suite: simple_stmt | _NEWLINE _INDENT stmt+ _DEDENT
    
    // Comprehensions
    ?comp_for: ["async"] "for" exprlist "in" or_test [comp_iter]
    ?comp_iter: comp_for | comp_if
    ?comp_if: "if" test [comp_iter]
    ?exprlist: (expr|star_expr) ("," (expr|star_expr))* [","]
    ?star_expr: "*" expr
    
    // Dict and set makers
    ?dictorsetmaker: (test ":" test (comp_for | ("," test ":" test)* [","])) | (test (comp_for | ("," test)* [","]))
    
    // Numbers
    NUMBER: /0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+|\d+\.\d+|\d+/
    
    // Basic tokens
    NAME: /[a-zA-Z_]\w*/
    _NEWLINE: /\r?\n[\t ]*/
    COMMENT: /#[^\n]*/
    WS: /[ \t]+/
    
    AWAIT: "await"
    ASYNC: "async"
    
    %ignore WS
    %ignore COMMENT
    
    %import common.ESCAPED_STRING
    %import common.WS_INLINE
    
    %declare _INDENT _DEDENT
"""
