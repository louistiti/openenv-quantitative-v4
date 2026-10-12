"""Capability-restricted calculation worker. No task state, filesystem or network tools.
This is a bounded tool, not a general-purpose untrusted-code sandbox guarantee.
"""
import ast
import builtins
import json
import math
import resource
import statistics
import sys

MAX_OUTPUT = 4000
SAFE_BUILTINS = {name:getattr(builtins,name) for name in (
    'abs','all','any','bool','dict','divmod','enumerate','filter','float','int','isinstance',
    'len','list','map','max','min','next','pow','range','reversed','round','set','sorted','str','sum','tuple','zip',
    'Exception','ValueError','ZeroDivisionError')}
MODULES = {'math':math,'statistics':statistics}
METHODS = {'append','extend','pop','sort','reverse','count','index','items','keys','values','get',
           'copy','update','add','discard','remove','union','intersection','difference','real','imag',
           'conjugate','numerator','denominator','bit_length'}
ATTRIBUTES = METHODS | {k for m in MODULES.values() for k in dir(m) if not k.startswith('_')}
ALLOWED = (ast.Module,ast.Assign,ast.AnnAssign,ast.AugAssign,ast.Expr,ast.Name,ast.Load,ast.Store,
           ast.Constant,ast.List,ast.Tuple,ast.Set,ast.Dict,ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Compare,
           ast.If,ast.IfExp,ast.For,ast.While,ast.Break,ast.Continue,ast.Pass,ast.FunctionDef,ast.arguments,
           ast.arg,ast.Lambda,ast.Return,ast.Call,ast.keyword,ast.Attribute,ast.Subscript,ast.Slice,ast.ListComp,
           ast.SetComp,ast.DictComp,ast.GeneratorExp,ast.comprehension,ast.Import,ast.ImportFrom,ast.alias,
           ast.Try,ast.ExceptHandler,ast.Raise,ast.operator,ast.unaryop,ast.boolop,ast.cmpop)


def validate(code):
    tree=ast.parse(code)
    nodes=list(ast.walk(tree))
    if len(nodes)>3500: raise ValueError('Calculation too complex')
    for node in nodes:
        if not isinstance(node,ALLOWED): raise ValueError('Unsupported Python syntax')
        if isinstance(node,ast.Name) and (node.id.startswith('_') and node.id != '_'): raise ValueError('Private names blocked')
        if isinstance(node,ast.arg) and (node.arg.startswith('_') and node.arg != '_'): raise ValueError('Private names blocked')
        if isinstance(node,ast.FunctionDef) and (node.name.startswith('_') or node.decorator_list): raise ValueError('Decorators/private functions blocked')
        if isinstance(node,ast.Attribute) and (node.attr.startswith('_') or node.attr not in ATTRIBUTES): raise ValueError('Attribute unavailable')
        if isinstance(node,ast.Import):
            if any(a.name not in MODULES or (a.asname and a.asname.startswith('_')) for a in node.names): raise ValueError('Only math and statistics imports available')
        if isinstance(node,ast.ImportFrom):
            if node.level or node.module not in MODULES: raise ValueError('Only math and statistics imports available')
            if any(a.name.startswith('_') or a.name not in ATTRIBUTES or (a.asname and a.asname.startswith('_')) for a in node.names): raise ValueError('Import unavailable')
    return tree


def safe_import(name,globals=None,locals=None,fromlist=(),level=0):
    if level or name not in MODULES: raise ValueError('Import unavailable')
    return MODULES[name]


def main():
    resource.setrlimit(resource.RLIMIT_CPU,(3,3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
    resource.setrlimit(resource.RLIMIT_NOFILE,(32,32))
    if sys.platform.startswith('linux'):
        resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
    captured=[];size=0
    def safe_print(*args,sep=' ',end='\n'):
        nonlocal size
        if not isinstance(sep,str) or not isinstance(end,str): raise ValueError('print separators must be strings')
        text=sep.join(str(a) for a in args)+end
        size+=len(text)
        if size>MAX_OUTPUT: raise ValueError('Output limit exceeded')
        captured.append(text)
    code=sys.stdin.read(16001)
    try:
        if len(code)>16000: raise ValueError('Code limit exceeded')
        tree=validate(code)
        namespace={'__builtins__':{**SAFE_BUILTINS,'print':safe_print,'__import__':safe_import}}
        exec(compile(tree,'<calculation>','exec'),namespace,namespace)
        print(json.dumps({'ok':True,'stdout':''.join(captured)}))
    except BaseException as exc:
        # No tracebacks, host paths, source context or introspection in feedback.
        print(json.dumps({'ok':False,'error':type(exc).__name__,'stdout':''.join(captured)[:MAX_OUTPUT]}))

if __name__=='__main__': main()
