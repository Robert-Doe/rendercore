"""
Module 18 — A Toy JS Interpreter
====================================
Proves: a real tokenizer, a real recursive-descent parser, and a real
tree-walking evaluator — no embedded engine (no V8, no Duktape, no
QuickJS) — can run a real subset of JavaScript: variables, arithmetic,
string concatenation, if/else, while, for, functions, recursion, and
real lexical closures.

Deliberately NOT implemented: objects, arrays, ++/--, type coercion in
== / !=, prototypes, exceptions (try/catch), async/await. See
DECISIONS.md for why each is scoped out.

This module knows NOTHING about the DOM. That's the whole point — see
Module 0's DECISIONS.md §7. Module 19 builds the bridge.
"""

from dataclasses import dataclass, field


# ============================================================ TOKENIZER

KEYWORDS = {"let", "var", "function", "if", "else", "while", "for",
            "return", "true", "false", "null"}
TWO_CHAR_OPS = {"==", "!=", "<=", ">=", "&&", "||"}
ONE_CHAR_OPS = set("+-*/%=<>!(){};,")


@dataclass
class Token:
    type: str    # 'NUMBER' | 'STRING' | 'IDENT' | 'KEYWORD' | 'OP' | 'EOF'
    value: object


def tokenize(src: str) -> list:
    tokens = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t\r\n":
            i += 1
            continue
        if src[i:i + 2] == "//":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c.isdigit():
            start = i
            while i < n and (src[i].isdigit() or src[i] == "."):
                i += 1
            tokens.append(Token("NUMBER", float(src[start:i])))
            continue
        if c in "\"'":
            quote = c
            i += 1
            start = i
            while i < n and src[i] != quote:
                i += 1
            tokens.append(Token("STRING", src[start:i]))
            i += 1   # skip closing quote
            continue
        if c.isalpha() or c == "_":
            start = i
            while i < n and (src[i].isalnum() or src[i] == "_"):
                i += 1
            word = src[start:i]
            tokens.append(Token("KEYWORD" if word in KEYWORDS else "IDENT", word))
            continue
        two = src[i:i + 2]
        if two in TWO_CHAR_OPS:
            tokens.append(Token("OP", two))
            i += 2
            continue
        if c in ONE_CHAR_OPS:
            tokens.append(Token("OP", c))
            i += 1
            continue
        raise SyntaxError(f"unexpected character {c!r} at position {i}")
    tokens.append(Token("EOF", None))
    return tokens


# ==================================================================== AST

@dataclass
class Program: statements: list
@dataclass
class VarDecl: name: str; init: object
@dataclass
class ExprStmt: expr: object
@dataclass
class If: cond: object; then_body: list; else_body: object
@dataclass
class While: cond: object; body: list
@dataclass
class For: init: object; cond: object; update: object; body: list
@dataclass
class FunctionDecl: name: str; params: list; body: list
@dataclass
class Return: expr: object
@dataclass
class BlockStmt: statements: list
@dataclass
class BinOp: op: str; left: object; right: object
@dataclass
class UnaryOp: op: str; expr: object
@dataclass
class Num: value: float
@dataclass
class Str: value: str
@dataclass
class Bool: value: bool
@dataclass
class Null: pass
@dataclass
class Ident: name: str
@dataclass
class Assign: name: str; expr: object
@dataclass
class Call: callee: object; args: list


# ==================================================================== PARSER

class Parser:
    """Recursive descent, with one method per precedence LEVEL, from
    lowest (assignment) to highest (primary) — each level calls the one
    above it for its operands, which is what makes `2 + 3 * 4` correctly
    parse as `2 + (3 * 4)` without an explicit precedence table."""

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def check(self, type_: str, value=None) -> bool:
        t = self.peek()
        if t.type != type_:
            return False
        return value is None or t.value == value

    def expect(self, type_: str, value=None) -> Token:
        if not self.check(type_, value):
            t = self.peek()
            raise SyntaxError(f"expected {type_} {value!r}, got {t.type} {t.value!r}")
        return self.advance()

    # ---- statements ----

    def parse_program(self) -> Program:
        statements = []
        while not self.check("EOF"):
            statements.append(self.parse_statement())
        return Program(statements)

    def parse_statement(self):
        if self.check("KEYWORD", "let") or self.check("KEYWORD", "var"):
            return self.parse_var_decl()
        if self.check("KEYWORD", "if"):
            return self.parse_if()
        if self.check("KEYWORD", "while"):
            return self.parse_while()
        if self.check("KEYWORD", "for"):
            return self.parse_for()
        if self.check("KEYWORD", "function"):
            return self.parse_function_decl()
        if self.check("KEYWORD", "return"):
            return self.parse_return()
        if self.check("OP", "{"):
            return BlockStmt(self.parse_block())
        return self.parse_expr_stmt()

    def parse_var_decl(self) -> VarDecl:
        self.advance()   # 'let' or 'var'
        name = self.expect("IDENT").value
        init = None
        if self.check("OP", "="):
            self.advance()
            init = self.parse_expression()
        self.expect("OP", ";")
        return VarDecl(name, init)

    def parse_block(self) -> list:
        self.expect("OP", "{")
        statements = []
        while not self.check("OP", "}"):
            statements.append(self.parse_statement())
        self.expect("OP", "}")
        return statements

    def parse_if(self) -> If:
        self.advance()
        self.expect("OP", "(")
        cond = self.parse_expression()
        self.expect("OP", ")")
        then_body = self.parse_block()
        else_body = None
        if self.check("KEYWORD", "else"):
            self.advance()
            else_body = [self.parse_if()] if self.check("KEYWORD", "if") else self.parse_block()
        return If(cond, then_body, else_body)

    def parse_while(self) -> While:
        self.advance()
        self.expect("OP", "(")
        cond = self.parse_expression()
        self.expect("OP", ")")
        return While(cond, self.parse_block())

    def parse_for(self) -> For:
        self.advance()
        self.expect("OP", "(")
        init = None
        if self.check("OP", ";"):
            self.advance()
        elif self.check("KEYWORD", "let") or self.check("KEYWORD", "var"):
            init = self.parse_var_decl()   # consumes its own trailing ';'
        else:
            init = ExprStmt(self.parse_expression())
            self.expect("OP", ";")
        cond = None if self.check("OP", ";") else self.parse_expression()
        self.expect("OP", ";")
        update = None if self.check("OP", ")") else self.parse_expression()
        self.expect("OP", ")")
        return For(init, cond, update, self.parse_block())

    def parse_function_decl(self) -> FunctionDecl:
        self.advance()
        name = self.expect("IDENT").value
        self.expect("OP", "(")
        params = []
        if not self.check("OP", ")"):
            params.append(self.expect("IDENT").value)
            while self.check("OP", ","):
                self.advance()
                params.append(self.expect("IDENT").value)
        self.expect("OP", ")")
        return FunctionDecl(name, params, self.parse_block())

    def parse_return(self) -> Return:
        self.advance()
        expr = None if self.check("OP", ";") else self.parse_expression()
        self.expect("OP", ";")
        return Return(expr)

    def parse_expr_stmt(self) -> ExprStmt:
        expr = self.parse_expression()
        self.expect("OP", ";")
        return ExprStmt(expr)

    # ---- expressions, lowest to highest precedence ----

    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_or()
        if self.check("OP", "="):
            self.advance()
            value = self.parse_assignment()   # right-associative: a = b = c
            if not isinstance(left, Ident):
                raise SyntaxError("invalid assignment target")
            return Assign(left.name, value)
        return left

    def _left_assoc(self, next_level, *ops):
        left = next_level()
        while self.peek().type == "OP" and self.peek().value in ops:
            op = self.advance().value
            left = BinOp(op, left, next_level())
        return left

    def parse_or(self):
        return self._left_assoc(self.parse_and, "||")

    def parse_and(self):
        return self._left_assoc(self.parse_equality, "&&")

    def parse_equality(self):
        return self._left_assoc(self.parse_relational, "==", "!=")

    def parse_relational(self):
        return self._left_assoc(self.parse_additive, "<", ">", "<=", ">=")

    def parse_additive(self):
        return self._left_assoc(self.parse_multiplicative, "+", "-")

    def parse_multiplicative(self):
        return self._left_assoc(self.parse_unary, "*", "/", "%")

    def parse_unary(self):
        if self.check("OP", "!") or self.check("OP", "-"):
            op = self.advance().value
            return UnaryOp(op, self.parse_unary())
        return self.parse_call()

    def parse_call(self):
        expr = self.parse_primary()
        while self.check("OP", "("):
            self.advance()
            args = []
            if not self.check("OP", ")"):
                args.append(self.parse_expression())
                while self.check("OP", ","):
                    self.advance()
                    args.append(self.parse_expression())
            self.expect("OP", ")")
            expr = Call(expr, args)
        return expr

    def parse_primary(self):
        t = self.peek()
        if t.type == "NUMBER":
            self.advance(); return Num(t.value)
        if t.type == "STRING":
            self.advance(); return Str(t.value)
        if t.type == "KEYWORD" and t.value == "true":
            self.advance(); return Bool(True)
        if t.type == "KEYWORD" and t.value == "false":
            self.advance(); return Bool(False)
        if t.type == "KEYWORD" and t.value == "null":
            self.advance(); return Null()
        if t.type == "IDENT":
            self.advance(); return Ident(t.value)
        if t.type == "OP" and t.value == "(":
            self.advance()
            expr = self.parse_expression()
            self.expect("OP", ")")
            return expr
        raise SyntaxError(f"unexpected token {t.type} {t.value!r}")


def parse(src: str) -> Program:
    return Parser(tokenize(src)).parse_program()


# ================================================================ EVALUATOR

class Environment:
    """A lexical scope: its own variables, plus a link to the scope it
    was created inside. Lookups walk outward until found, or fail."""

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def declare(self, name, value):
        self.vars[name] = value

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"{name} is not defined")

    def set_existing(self, name, value):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.set_existing(name, value)
            return
        raise NameError(f"{name} is not defined")


@dataclass
class Function:
    name: str
    params: list
    body: list
    closure_env: Environment   # the scope the function was DEFINED in — this
                                 # is what makes closures work correctly


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


def truthy(value) -> bool:
    return value not in (None, False, 0, "", 0.0)


def js_str(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.output = []
        self.global_env.declare("print", lambda *args: self.output.append(
            " ".join(js_str(a) for a in args)))

    def run(self, program: Program):
        self.exec_block(program.statements, self.global_env)

    def exec_block(self, statements, env):
        for stmt in statements:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, stmt, env):
        return getattr(self, f"exec_{type(stmt).__name__}")(stmt, env)

    def exec_VarDecl(self, s, env):
        env.declare(s.name, self.eval_expr(s.init, env) if s.init is not None else None)

    def exec_ExprStmt(self, s, env):
        self.eval_expr(s.expr, env)

    def exec_BlockStmt(self, s, env):
        self.exec_block(s.statements, Environment(env))

    def exec_If(self, s, env):
        if truthy(self.eval_expr(s.cond, env)):
            self.exec_block(s.then_body, Environment(env))
        elif s.else_body is not None:
            self.exec_block(s.else_body, Environment(env))

    def exec_While(self, s, env):
        while truthy(self.eval_expr(s.cond, env)):
            self.exec_block(s.body, Environment(env))

    def exec_For(self, s, env):
        loop_env = Environment(env)
        if s.init is not None:
            self.exec_stmt(s.init, loop_env)
        while s.cond is None or truthy(self.eval_expr(s.cond, loop_env)):
            self.exec_block(s.body, Environment(loop_env))
            if s.update is not None:
                self.eval_expr(s.update, loop_env)

    def exec_FunctionDecl(self, s, env):
        env.declare(s.name, Function(s.name, s.params, s.body, env))

    def exec_Return(self, s, env):
        raise ReturnSignal(self.eval_expr(s.expr, env) if s.expr is not None else None)

    def eval_expr(self, expr, env):
        return getattr(self, f"eval_{type(expr).__name__}")(expr, env)

    def eval_Num(self, e, env): return e.value
    def eval_Str(self, e, env): return e.value
    def eval_Bool(self, e, env): return e.value
    def eval_Null(self, e, env): return None
    def eval_Ident(self, e, env): return env.get(e.name)

    def eval_Assign(self, e, env):
        value = self.eval_expr(e.expr, env)
        env.set_existing(e.name, value)
        return value

    def eval_UnaryOp(self, e, env):
        value = self.eval_expr(e.expr, env)
        if e.op == "-":
            return -value
        if e.op == "!":
            return not truthy(value)
        raise SyntaxError(f"unknown unary operator {e.op!r}")

    def eval_BinOp(self, e, env):
        if e.op == "&&":
            left = self.eval_expr(e.left, env)
            return left if not truthy(left) else self.eval_expr(e.right, env)
        if e.op == "||":
            left = self.eval_expr(e.left, env)
            return left if truthy(left) else self.eval_expr(e.right, env)

        left = self.eval_expr(e.left, env)
        right = self.eval_expr(e.right, env)
        if e.op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return js_str(left) + js_str(right)   # JS-like loose "+"
            return left + right
        if e.op == "-": return left - right
        if e.op == "*": return left * right
        if e.op == "/": return left / right
        if e.op == "%": return left % right
        if e.op == "==": return left == right   # NOTE: strict, no type coercion — see DECISIONS.md
        if e.op == "!=": return left != right
        if e.op == "<": return left < right
        if e.op == ">": return left > right
        if e.op == "<=": return left <= right
        if e.op == ">=": return left >= right
        raise SyntaxError(f"unknown binary operator {e.op!r}")

    def eval_Call(self, e, env):
        callee = self.eval_expr(e.callee, env)
        args = [self.eval_expr(a, env) for a in e.args]
        if isinstance(callee, Function):
            # Lexical scoping: the new call's scope is created INSIDE the
            # function's closure_env (where it was DEFINED), never inside
            # the caller's env (where it's being CALLED from). This one
            # line is the entire closure mechanism.
            call_env = Environment(callee.closure_env)
            for param, arg in zip(callee.params, args):
                call_env.declare(param, arg)
            try:
                self.exec_block(callee.body, call_env)
            except ReturnSignal as r:
                return r.value
            return None
        if callable(callee):
            return callee(*args)
        raise TypeError(f"{callee!r} is not callable")


def run(source: str) -> Interpreter:
    interp = Interpreter()
    interp.run(parse(source))
    return interp


if __name__ == "__main__":
    source = """
    function factorial(n) {
      if (n <= 1) {
        return 1;
      }
      return n * factorial(n - 1);
    }
    print(factorial(6));

    let total = 0;
    for (let i = 1; i <= 10; i = i + 1) {
      total = total + i;
    }
    print(total);

    let count = 0;
    while (count < 5) {
      count = count + 1;
    }
    print(count);

    print("Hello, " + "World!");

    function makeCounter() {
      let n = 0;
      function increment() {
        n = n + 1;
        return n;
      }
      return increment;
    }
    let counter1 = makeCounter();
    counter1();
    counter1();
    print(counter1());

    let counter2 = makeCounter();
    print(counter2());
    """

    interp = run(source)

    print("=" * 70)
    print("Interpreter output (via the JS program's own print() calls)")
    print("=" * 70)
    for line in interp.output:
        print(f"  {line}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"factorial(6) == 720 (recursion works): {interp.output[0] == '720'}")
    print(f"sum of 1..10 via a for-loop == 55: {interp.output[1] == '55'}")
    print(f"while loop counted to 5: {interp.output[2] == '5'}")
    print(f"string concatenation: {interp.output[3] == 'Hello, World!'}")
    print(f"counter1 called 3 times total, shows 3: {interp.output[4] == '3'}")
    print(f"counter2 is an INDEPENDENT closure, starts fresh at 1 "
          f"(not affected by counter1's calls): {interp.output[5] == '1'}")
