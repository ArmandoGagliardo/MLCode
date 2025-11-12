"""
Call Graph Builder v2.0
========================

Analisi avanzata del progetto con:
- Tutte le classi con metodi dettagliati
- Chi chiama chi (call graph completo)
- Return types e type hints
- Dependency injection tracking
- Interface implementations
- Design pattern detection
- Complexity metrics
- Cross-reference tra componenti

Output: .agent/cache/call_graph_v2.json e call_graph_v2.md
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ParameterInfo:
    """Informazioni su un parametro"""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None
    is_varargs: bool = False
    is_kwargs: bool = False


@dataclass
class MethodInfo:
    """Informazioni dettagliate su un metodo"""
    name: str
    file: str
    line: int
    params: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_async: bool = False
    is_property: bool = False
    is_staticmethod: bool = False
    is_classmethod: bool = False
    is_abstract: bool = False
    calls: List[str] = field(default_factory=list)  # Funzioni chiamate da questo metodo
    complexity: int = 0  # Cyclomatic complexity


@dataclass
class ClassInfo:
    """Informazioni dettagliate su una classe"""
    name: str
    full_name: str  # file::class
    file: str
    line: int
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    methods: List[MethodInfo] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    class_variables: List[Tuple[str, Optional[str]]] = field(default_factory=list)  # (name, type)
    is_abstract: bool = False
    is_dataclass: bool = False
    implements_interfaces: List[str] = field(default_factory=list)
    used_by: List[str] = field(default_factory=list)  # Chi usa questa classe


@dataclass
class FunctionInfo:
    """Informazioni su funzione standalone"""
    name: str
    full_name: str  # file::function
    file: str
    line: int
    params: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_async: bool = False
    calls: List[str] = field(default_factory=list)
    complexity: int = 0


@dataclass
class CallInfo:
    """Informazioni su una chiamata"""
    caller: str  # file::class::method o file::function
    target: str  # nome funzione/metodo chiamato
    file: str
    line: int
    args_count: int = 0
    has_kwargs: bool = False
    context: str = ""  # Contesto della chiamata (if, loop, try, ecc.)


class EnhancedCallGraphAnalyzer:
    """Analizzatore avanzato del call graph"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.classes: Dict[str, ClassInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}
        self.calls: List[CallInfo] = []
        self.interfaces: Dict[str, ClassInfo] = {}  # Classi che sono interfacce
        self.implementations: Dict[str, List[str]] = defaultdict(list)  # interface -> [implementations]
        self.inheritance_tree: Dict[str, List[str]] = defaultdict(list)  # base -> [children]

    def analyze_project(self) -> Dict[str, Any]:
        """Analizza l'intero progetto"""
        logger.info("Starting enhanced call graph analysis...")

        # Trova tutti i file Python nelle directory architetturali
        directories = ['domain', 'application', 'infrastructure', 'presentation']
        py_files = []

        for directory in directories:
            dir_path = self.project_root / directory
            if dir_path.exists():
                py_files.extend(dir_path.rglob("*.py"))

        logger.info(f"Found {len(py_files)} Python files")

        # Prima passata: estrai classi e funzioni
        for py_file in py_files:
            self._analyze_file(py_file)

        # Seconda passata: analizza ereditarietà e implementazioni
        self._analyze_inheritance()

        # Terza passata: identifica design patterns
        patterns = self._detect_patterns()

        # Compute metrics
        metrics = self._compute_metrics()

        result = {
            'classes': {k: asdict(v) for k, v in self.classes.items()},
            'functions': {k: asdict(v) for k, v in self.functions.items()},
            'calls': [asdict(c) for c in self.calls],
            'interfaces': {k: asdict(v) for k, v in self.interfaces.items()},
            'implementations': dict(self.implementations),
            'inheritance_tree': dict(self.inheritance_tree),
            'design_patterns': patterns,
            'metrics': metrics
        }

        return result

    def _analyze_file(self, file_path: Path):
        """Analizza un singolo file"""
        try:
            rel_path = str(file_path.relative_to(self.project_root))
            logger.info(f"Analyzing: {rel_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            visitor = EnhancedVisitor(rel_path, self)
            visitor.visit(tree)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    def _analyze_inheritance(self):
        """Analizza ereditarietà e implementazioni"""
        for full_name, cls_info in self.classes.items():
            for base in cls_info.bases:
                # Trova la classe base
                base_full_name = self._resolve_class_name(base, cls_info.file)
                if base_full_name:
                    self.inheritance_tree[base_full_name].append(full_name)

                    # Check se è un'interfaccia (nel layer domain/interfaces)
                    base_cls = self.classes.get(base_full_name)
                    if base_cls and 'interfaces' in base_cls.file:
                        cls_info.implements_interfaces.append(base)
                        self.interfaces[base_full_name] = base_cls
                        self.implementations[base_full_name].append(full_name)

    def _resolve_class_name(self, class_name: str, current_file: str) -> Optional[str]:
        """Risolve il nome completo di una classe"""
        # Cerca nelle classi già trovate
        for full_name, cls_info in self.classes.items():
            if cls_info.name == class_name:
                return full_name
        return None

    def _detect_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Identifica design patterns comuni"""
        patterns = {
            'factory': [],
            'singleton': [],
            'repository': [],
            'service': [],
            'strategy': [],
            'observer': [],
            'dependency_injection': []
        }

        for full_name, cls_info in self.classes.items():
            name = cls_info.name.lower()

            # Factory pattern
            if 'factory' in name or any('create' in m.name.lower() for m in cls_info.methods):
                patterns['factory'].append({
                    'class': full_name,
                    'file': cls_info.file,
                    'confidence': 'high' if 'factory' in name else 'medium'
                })

            # Singleton pattern
            if any(d == 'singleton' for d in cls_info.decorators):
                patterns['singleton'].append({
                    'class': full_name,
                    'file': cls_info.file,
                    'confidence': 'high'
                })

            # Repository pattern
            if 'repository' in name or any('repository' in b.lower() for b in cls_info.bases):
                patterns['repository'].append({
                    'class': full_name,
                    'file': cls_info.file,
                    'confidence': 'high' if 'repository' in name else 'medium'
                })

            # Service pattern
            if 'service' in name and cls_info.file.startswith('application'):
                patterns['service'].append({
                    'class': full_name,
                    'file': cls_info.file,
                    'confidence': 'high'
                })

            # Strategy pattern (implementa interfaccia)
            if cls_info.implements_interfaces:
                patterns['strategy'].append({
                    'class': full_name,
                    'interfaces': cls_info.implements_interfaces,
                    'file': cls_info.file,
                    'confidence': 'high'
                })

            # Dependency Injection (costruttore con molti parametri)
            init_method = next((m for m in cls_info.methods if m.name == '__init__'), None)
            if init_method and len(init_method.params) > 3:
                patterns['dependency_injection'].append({
                    'class': full_name,
                    'dependencies': len(init_method.params) - 1,  # -1 per self
                    'file': cls_info.file,
                    'confidence': 'high'
                })

        return patterns

    def _compute_metrics(self) -> Dict[str, Any]:
        """Calcola metriche del codice"""
        total_classes = len(self.classes)
        total_methods = sum(len(c.methods) for c in self.classes.values())
        total_functions = len(self.functions)
        total_calls = len(self.calls)

        # Complexity metrics
        avg_methods_per_class = total_methods / total_classes if total_classes > 0 else 0
        max_methods = max((len(c.methods) for c in self.classes.values()), default=0)

        # Most complex classes (per numero di metodi)
        complex_classes = sorted(
            [(name, len(cls.methods)) for name, cls in self.classes.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Funzioni più chiamate
        call_counts = defaultdict(int)
        for call in self.calls:
            call_counts[call.target] += 1

        most_called = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        # Interface adherence
        interface_impl_count = sum(len(impls) for impls in self.implementations.values())

        # Inheritance depth
        max_depth = self._compute_max_inheritance_depth()

        return {
            'total_classes': total_classes,
            'total_methods': total_methods,
            'total_functions': total_functions,
            'total_calls': total_calls,
            'avg_methods_per_class': round(avg_methods_per_class, 2),
            'max_methods_in_class': max_methods,
            'most_complex_classes': [{'name': name, 'methods': count} for name, count in complex_classes],
            'most_called_functions': [{'name': name, 'calls': count} for name, count in most_called],
            'total_interfaces': len(self.interfaces),
            'total_implementations': interface_impl_count,
            'max_inheritance_depth': max_depth,
            'classes_with_di': len([c for c in self.classes.values()
                                   if any(len(m.params) > 3 for m in c.methods if m.name == '__init__')])
        }

    def _compute_max_inheritance_depth(self) -> int:
        """Calcola la massima profondità di ereditarietà"""
        def get_depth(class_name: str, visited: Set[str]) -> int:
            if class_name in visited:
                return 0
            visited.add(class_name)

            children = self.inheritance_tree.get(class_name, [])
            if not children:
                return 0

            return 1 + max((get_depth(child, visited.copy()) for child in children), default=0)

        max_depth = 0
        for class_name in self.classes.keys():
            depth = get_depth(class_name, set())
            max_depth = max(max_depth, depth)

        return max_depth


class EnhancedVisitor(ast.NodeVisitor):
    """Visitor AST avanzato"""

    def __init__(self, file_path: str, analyzer: EnhancedCallGraphAnalyzer):
        self.file_path = file_path
        self.analyzer = analyzer
        self.current_class: Optional[str] = None
        self.current_method: Optional[str] = None
        self.scope_stack: List[Tuple[str, str]] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visita definizione classe"""
        class_full_name = f"{self.file_path}::{node.name}"
        self.current_class = node.name

        # Estrai informazioni
        bases = [self._get_name(base) for base in node.bases]
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Check se è dataclass
        is_dataclass = 'dataclass' in decorators

        # Check se è abstract
        is_abstract = 'ABC' in bases or 'abstractmethod' in ' '.join(decorators)

        # Estrai variabili di classe
        class_vars = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                var_name = item.target.id
                var_type = self._get_annotation(item.annotation) if item.annotation else None
                class_vars.append((var_name, var_type))

        # Estrai metodi
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_method_info(item)
                methods.append(method_info)

        # Crea ClassInfo
        cls_info = ClassInfo(
            name=node.name,
            full_name=class_full_name,
            file=self.file_path,
            line=node.lineno,
            bases=bases,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            methods=methods,
            class_variables=class_vars,
            is_abstract=is_abstract,
            is_dataclass=is_dataclass
        )

        self.analyzer.classes[class_full_name] = cls_info

        # Visita figli
        self.scope_stack.append(('class', node.name))
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visita funzione"""
        if self.current_class:
            # È un metodo, già gestito
            return

        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visita funzione async"""
        if self.current_class:
            return

        self._visit_function(node, is_async=True)

    def _visit_function(self, node, is_async: bool):
        """Visita funzione standalone"""
        func_full_name = f"{self.file_path}::{node.name}"
        self.current_method = node.name

        params = self._extract_parameters(node.args)
        return_type = self._get_annotation(node.returns) if node.returns else None
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Calcola complexity
        complexity = self._calculate_complexity(node)

        # Estrai chiamate nel corpo
        calls = self._extract_calls_from_body(node)

        func_info = FunctionInfo(
            name=node.name,
            full_name=func_full_name,
            file=self.file_path,
            line=node.lineno,
            params=params,
            return_type=return_type,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            is_async=is_async,
            calls=calls,
            complexity=complexity
        )

        self.analyzer.functions[func_full_name] = func_info

        self.scope_stack.append(('function', node.name))
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_method = None

    def _extract_method_info(self, node) -> MethodInfo:
        """Estrae informazioni dettagliate da un metodo"""
        params = self._extract_parameters(node.args)
        return_type = self._get_annotation(node.returns) if node.returns else None
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Check decoratori speciali
        is_property = 'property' in decorators
        is_staticmethod = 'staticmethod' in decorators
        is_classmethod = 'classmethod' in decorators
        is_abstract = 'abstractmethod' in decorators

        # Calcola complexity
        complexity = self._calculate_complexity(node)

        # Estrai chiamate
        calls = self._extract_calls_from_body(node)

        return MethodInfo(
            name=node.name,
            file=self.file_path,
            line=node.lineno,
            params=params,
            return_type=return_type,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_property=is_property,
            is_staticmethod=is_staticmethod,
            is_classmethod=is_classmethod,
            is_abstract=is_abstract,
            calls=calls,
            complexity=complexity
        )

    def _extract_parameters(self, args: ast.arguments) -> List[ParameterInfo]:
        """Estrae parametri con dettagli"""
        params = []

        # Parametri normali
        for i, arg in enumerate(args.args):
            default_value = None
            if args.defaults:
                default_index = i - (len(args.args) - len(args.defaults))
                if default_index >= 0:
                    default_value = self._get_default_value(args.defaults[default_index])

            params.append(ParameterInfo(
                name=arg.arg,
                type_hint=self._get_annotation(arg.annotation) if arg.annotation else None,
                default_value=default_value
            ))

        # *args
        if args.vararg:
            params.append(ParameterInfo(
                name=args.vararg.arg,
                type_hint=self._get_annotation(args.vararg.annotation) if args.vararg.annotation else None,
                is_varargs=True
            ))

        # **kwargs
        if args.kwarg:
            params.append(ParameterInfo(
                name=args.kwarg.arg,
                type_hint=self._get_annotation(args.kwarg.annotation) if args.kwarg.annotation else None,
                is_kwargs=True
            ))

        return params

    def _calculate_complexity(self, node) -> int:
        """Calcola cyclomatic complexity"""
        complexity = 1  # Base

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _extract_calls_from_body(self, node) -> List[str]:
        """Estrae tutte le chiamate dal corpo di una funzione"""
        calls = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = self._get_call_name(child.func)
                if func_name:
                    calls.append(func_name)

        return calls

    def visit_Call(self, node: ast.Call):
        """Visita chiamata funzione"""
        func_name = self._get_call_name(node.func)

        if func_name:
            # Determina caller
            caller = None
            if self.scope_stack:
                scope_type, scope_name = self.scope_stack[-1]
                if scope_type == 'class':
                    caller = f"{self.file_path}::{scope_name}"
                elif scope_type == 'function':
                    caller = f"{self.file_path}::{scope_name}"

            call_info = CallInfo(
                caller=caller or self.file_path,
                target=func_name,
                file=self.file_path,
                line=node.lineno,
                args_count=len(node.args),
                has_kwargs=len(node.keywords) > 0
            )

            self.analyzer.calls.append(call_info)

        self.generic_visit(node)

    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        """Estrae nome chiamata"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        return None

    def _get_name(self, node: ast.AST) -> str:
        """Estrae nome da nodo AST"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        return ""

    def _get_annotation(self, node: ast.AST) -> str:
        """Estrae type annotation"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation(node.value)
            slice_val = self._get_annotation(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._get_annotation(e) for e in node.elts]
            return f"({', '.join(elements)})"
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # Union types (Python 3.10+)
            left = self._get_annotation(node.left)
            right = self._get_annotation(node.right)
            return f"{left} | {right}"
        return str(type(node).__name__)

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Estrae nome decorator"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_name(decorator.func)
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        return str(decorator)

    def _get_default_value(self, node: ast.AST) -> str:
        """Estrae valore default di un parametro"""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return "[]"
        elif isinstance(node, ast.Dict):
            return "{}"
        elif isinstance(node, ast.Call):
            func_name = self._get_call_name(node.func)
            return f"{func_name}(...)"
        return "..."


def main():
    """Entry point"""
    project_root = Path(__file__).parent
    cache_dir = project_root / '.agent' / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Analizza call graph
    analyzer = EnhancedCallGraphAnalyzer(project_root)

    try:
        call_graph = analyzer.analyze_project()

        # Salva JSON
        json_file = cache_dir / 'call_graph_v2.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(call_graph, f, indent=2, ensure_ascii=False)

        logger.info(f"[OK] Enhanced call graph JSON saved to: {json_file}")

        # Stampa statistiche
        metrics = call_graph['metrics']
        patterns = call_graph['design_patterns']

        print("\n" + "=" * 80)
        print("ENHANCED CALL GRAPH ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\n[STATS] Statistics:")
        print(f"  Total Classes:           {metrics['total_classes']}")
        print(f"  Total Methods:           {metrics['total_methods']}")
        print(f"  Total Functions:         {metrics['total_functions']}")
        print(f"  Total Calls Tracked:     {metrics['total_calls']}")
        print(f"  Avg Methods/Class:       {metrics['avg_methods_per_class']}")
        print(f"  Max Methods in Class:    {metrics['max_methods_in_class']}")
        print(f"  Total Interfaces:        {metrics['total_interfaces']}")
        print(f"  Total Implementations:   {metrics['total_implementations']}")
        print(f"  Max Inheritance Depth:   {metrics['max_inheritance_depth']}")
        print(f"  Classes with DI:         {metrics['classes_with_di']}")

        print(f"\n[PATTERNS] Design Patterns Detected:")
        for pattern_name, instances in patterns.items():
            if instances:
                print(f"  {pattern_name.capitalize():20} {len(instances):3} instances")

        print(f"\n[COMPLEX] Most Complex Classes:")
        for item in metrics['most_complex_classes'][:5]:
            print(f"  {item['name']:60} {item['methods']:3} methods")

        print(f"\n[POPULAR] Most Called Functions:")
        for item in metrics['most_called_functions'][:10]:
            print(f"  {item['name']:40} {item['calls']:4} calls")

        print(f"\nOutput: {json_file}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
