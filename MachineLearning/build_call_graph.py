"""
Call Graph Builder
==================

Analizza il progetto e costruisce un grafo dettagliato di:
- Tutte le classi con metodi
- Chi chiama chi
- Type hints e return types
- Parametri e loro tipi

Output: .agent/cache/call_graph.json e call_graph.md
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CallGraphAnalyzer:
    """Analizza il call graph del progetto"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.call_graph: Dict[str, Any] = {}
        self.classes: Dict[str, Dict] = {}
        self.functions: Dict[str, Dict] = {}
        self.calls: List[Dict] = []

    def analyze_project(self, entry_point: str = None) -> Dict[str, Any]:
        """Analizza l'intero progetto"""
        logger.info("Starting call graph analysis...")

        # Trova tutti i file Python nelle directory principali
        directories = ['domain', 'application', 'infrastructure', 'presentation']
        py_files = []

        for directory in directories:
            dir_path = self.project_root / directory
            if dir_path.exists():
                py_files.extend(dir_path.rglob("*.py"))

        logger.info(f"Found {len(py_files)} Python files in architecture layers")

        # Analizza ogni file
        for py_file in py_files:
            self._analyze_file(py_file)

        # Costruisci il grafo finale
        result = {
            'classes': self.classes,
            'functions': self.functions,
            'calls': self.calls,
            'statistics': self._compute_statistics()
        }

        return result

    def _analyze_file(self, file_path: Path):
        """Analizza un singolo file Python"""
        try:
            rel_path = str(file_path.relative_to(self.project_root))
            logger.info(f"Analyzing: {rel_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            # Visita l'AST
            visitor = CallGraphVisitor(rel_path, self.classes, self.functions, self.calls)
            visitor.visit(tree)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    def _compute_statistics(self) -> Dict[str, Any]:
        """Calcola statistiche sul call graph"""
        total_classes = len(self.classes)
        total_methods = sum(len(cls['methods']) for cls in self.classes.values())
        total_functions = len(self.functions)
        total_calls = len(self.calls)

        # Trova funzioni più chiamate
        call_counts = defaultdict(int)
        for call in self.calls:
            target = call.get('target')
            if target:
                call_counts[target] += 1

        most_called = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            'total_classes': total_classes,
            'total_methods': total_methods,
            'total_functions': total_functions,
            'total_calls': total_calls,
            'most_called_functions': [{'name': name, 'calls': count} for name, count in most_called]
        }


class CallGraphVisitor(ast.NodeVisitor):
    """Visita l'AST per estrarre classi, funzioni e chiamate"""

    def __init__(self, file_path: str, classes: Dict, functions: Dict, calls: List):
        self.file_path = file_path
        self.classes = classes
        self.functions = functions
        self.calls = calls
        self.current_class = None
        self.current_function = None
        self.scope_stack = []

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visita una definizione di classe"""
        class_name = f"{self.file_path}::{node.name}"
        self.current_class = node.name

        # Estrai informazioni sulla classe
        bases = [self._get_name(base) for base in node.bases]
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Estrai metodi
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function_info(item, is_method=True)
                methods.append(method_info)

        self.classes[class_name] = {
            'name': node.name,
            'file': self.file_path,
            'line': node.lineno,
            'bases': bases,
            'decorators': decorators,
            'methods': methods,
            'docstring': ast.get_docstring(node)
        }

        # Visita i figli
        self.scope_stack.append(('class', node.name))
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visita una definizione di funzione"""
        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visita una definizione di funzione asincrona"""
        self._visit_function(node, is_async=True)

    def _visit_function(self, node, is_async: bool):
        """Visita una funzione (async o normale)"""
        # Se è un metodo, già gestito in visit_ClassDef
        if self.current_class:
            return

        func_name = f"{self.file_path}::{node.name}"
        self.current_function = node.name

        func_info = self._extract_function_info(node, is_method=False)
        func_info['is_async'] = is_async

        self.functions[func_name] = func_info

        # Visita il corpo della funzione per trovare chiamate
        self.scope_stack.append(('function', node.name))
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_function = None

    def visit_Call(self, node: ast.Call):
        """Visita una chiamata di funzione"""
        # Estrai il nome della funzione chiamata
        func_name = self._get_call_name(node.func)

        if func_name:
            # Determina il contesto (classe o funzione)
            context = None
            if self.scope_stack:
                scope_type, scope_name = self.scope_stack[-1]
                if scope_type == 'class':
                    context = f"{self.file_path}::{scope_name}"
                elif scope_type == 'function':
                    context = f"{self.file_path}::{scope_name}"

            # Estrai argomenti
            args = []
            for arg in node.args:
                args.append(self._get_arg_value(arg))

            kwargs = {}
            for keyword in node.keywords:
                kwargs[keyword.arg] = self._get_arg_value(keyword.value)

            call_info = {
                'caller': context,
                'target': func_name,
                'file': self.file_path,
                'line': node.lineno,
                'args': args,
                'kwargs': kwargs
            }

            self.calls.append(call_info)

        self.generic_visit(node)

    def _extract_function_info(self, node, is_method: bool) -> Dict[str, Any]:
        """Estrae informazioni dettagliate da una funzione"""
        # Parametri
        params = []
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': self._get_annotation(arg.annotation) if arg.annotation else None
            }
            params.append(param_info)

        # Return type
        return_type = self._get_annotation(node.returns) if node.returns else None

        # Decoratori
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Docstring
        docstring = ast.get_docstring(node)

        return {
            'name': node.name,
            'file': self.file_path,
            'line': node.lineno,
            'params': params,
            'return_type': return_type,
            'decorators': decorators,
            'docstring': docstring,
            'is_method': is_method
        }

    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        """Estrae il nome da una chiamata"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Call):
            return self._get_call_name(node.func)
        return None

    def _get_name(self, node: ast.AST) -> str:
        """Estrae il nome da un nodo AST"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        return ""

    def _get_annotation(self, node: ast.AST) -> str:
        """Estrae una type annotation"""
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
        return str(type(node).__name__)

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Estrae il nome di un decorator"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_name(decorator.func)
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        return str(decorator)

    def _get_arg_value(self, node: ast.AST) -> str:
        """Estrae il valore di un argomento"""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            func_name = self._get_call_name(node.func)
            return f"{func_name}(...)"
        return "..."


class MarkdownGenerator:
    """Genera markdown dal call graph"""

    def __init__(self, call_graph: Dict[str, Any]):
        self.graph = call_graph

    def generate(self) -> str:
        """Genera il markdown completo"""
        lines = []

        lines.append("# Call Graph Analysis")
        lines.append("")
        lines.append("Analisi completa delle classi, metodi, funzioni e chiamate nel progetto.")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Statistics
        lines.extend(self._generate_statistics())
        lines.append("")

        # Classes
        lines.extend(self._generate_classes())
        lines.append("")

        # Functions
        lines.extend(self._generate_functions())
        lines.append("")

        # Call relationships
        lines.extend(self._generate_calls())
        lines.append("")

        return "\n".join(lines)

    def _generate_statistics(self) -> List[str]:
        """Genera statistiche"""
        stats = self.graph['statistics']
        lines = []

        lines.append("## 📊 Statistics")
        lines.append("")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Classes | {stats['total_classes']} |")
        lines.append(f"| Total Methods | {stats['total_methods']} |")
        lines.append(f"| Total Functions | {stats['total_functions']} |")
        lines.append(f"| Total Function Calls | {stats['total_calls']} |")
        lines.append("")

        # Most called functions
        if stats['most_called_functions']:
            lines.append("### Most Called Functions")
            lines.append("")
            lines.append("| Function | Call Count |")
            lines.append("|----------|------------|")
            for item in stats['most_called_functions'][:10]:
                lines.append(f"| `{item['name']}` | {item['calls']} |")
            lines.append("")

        return lines

    def _generate_classes(self) -> List[str]:
        """Genera sezione classi"""
        lines = []
        lines.append("## 🏛️ Classes")
        lines.append("")

        # Raggruppa per layer
        classes_by_layer = defaultdict(list)
        for class_name, cls_data in self.graph['classes'].items():
            file = cls_data['file']
            if file.startswith('domain'):
                layer = 'Domain'
            elif file.startswith('application'):
                layer = 'Application'
            elif file.startswith('infrastructure'):
                layer = 'Infrastructure'
            elif file.startswith('presentation'):
                layer = 'Presentation'
            else:
                layer = 'Other'
            classes_by_layer[layer].append((class_name, cls_data))

        # Stampa per layer
        for layer in ['Domain', 'Application', 'Infrastructure', 'Presentation', 'Other']:
            if layer not in classes_by_layer:
                continue

            lines.append(f"### {layer} Layer")
            lines.append("")

            for class_name, cls_data in sorted(classes_by_layer[layer]):
                lines.append(f"#### `{cls_data['name']}`")
                lines.append("")
                lines.append(f"**File**: `{cls_data['file']}:{cls_data['line']}`")
                lines.append("")

                if cls_data['bases']:
                    lines.append(f"**Inherits**: {', '.join(f'`{b}`' for b in cls_data['bases'])}")
                    lines.append("")

                if cls_data['docstring']:
                    lines.append(f"**Description**: {cls_data['docstring'][:200]}")
                    lines.append("")

                if cls_data['methods']:
                    lines.append(f"**Methods** ({len(cls_data['methods'])}):")
                    lines.append("")

                    for method in cls_data['methods']:
                        # Signature
                        params_str = ", ".join(
                            f"{p['name']}: {p['type']}" if p['type'] else p['name']
                            for p in method['params']
                        )
                        return_str = f" -> {method['return_type']}" if method['return_type'] else ""
                        decorators_str = " ".join(f"@{d}" for d in method['decorators'])

                        if decorators_str:
                            lines.append(f"- {decorators_str}")
                        lines.append(f"  `{method['name']}({params_str}){return_str}`")

                        if method['docstring']:
                            doc_short = method['docstring'].split('\n')[0][:80]
                            lines.append(f"  - {doc_short}")

                        lines.append("")

                lines.append("---")
                lines.append("")

        return lines

    def _generate_functions(self) -> List[str]:
        """Genera sezione funzioni standalone"""
        lines = []
        lines.append("## 🔧 Standalone Functions")
        lines.append("")

        # Raggruppa per layer
        funcs_by_layer = defaultdict(list)
        for func_name, func_data in self.graph['functions'].items():
            file = func_data['file']
            if file.startswith('domain'):
                layer = 'Domain'
            elif file.startswith('application'):
                layer = 'Application'
            elif file.startswith('infrastructure'):
                layer = 'Infrastructure'
            elif file.startswith('presentation'):
                layer = 'Presentation'
            else:
                layer = 'Other'
            funcs_by_layer[layer].append((func_name, func_data))

        for layer in ['Domain', 'Application', 'Infrastructure', 'Presentation', 'Other']:
            if layer not in funcs_by_layer:
                continue

            lines.append(f"### {layer} Layer")
            lines.append("")

            for func_name, func_data in sorted(funcs_by_layer[layer]):
                params_str = ", ".join(
                    f"{p['name']}: {p['type']}" if p['type'] else p['name']
                    for p in func_data['params']
                )
                return_str = f" -> {func_data['return_type']}" if func_data['return_type'] else ""
                async_str = "async " if func_data.get('is_async') else ""

                lines.append(f"#### `{async_str}{func_data['name']}({params_str}){return_str}`")
                lines.append("")
                lines.append(f"**File**: `{func_data['file']}:{func_data['line']}`")
                lines.append("")

                if func_data['decorators']:
                    lines.append(f"**Decorators**: {', '.join(f'`@{d}`' for d in func_data['decorators'])}")
                    lines.append("")

                if func_data['docstring']:
                    lines.append(f"**Description**: {func_data['docstring'][:200]}")
                    lines.append("")

                lines.append("---")
                lines.append("")

        return lines

    def _generate_calls(self) -> List[str]:
        """Genera sezione chiamate"""
        lines = []
        lines.append("## 📞 Function Calls")
        lines.append("")

        # Raggruppa chiamate per caller
        calls_by_caller = defaultdict(list)
        for call in self.graph['calls']:
            caller = call.get('caller', 'Unknown')
            calls_by_caller[caller].append(call)

        lines.append(f"Total function calls tracked: {len(self.graph['calls'])}")
        lines.append("")

        # Mostra solo le prime 50 chiamate per non fare un file troppo grande
        if len(self.graph['calls']) > 50:
            lines.append("*Showing first 50 calls (see JSON for full list)*")
            lines.append("")

        lines.append("| Caller | Target | File:Line |")
        lines.append("|--------|--------|-----------|")

        for call in self.graph['calls'][:50]:
            caller = call.get('caller', 'Unknown')
            target = call.get('target', 'Unknown')
            location = f"{call['file']}:{call['line']}"
            lines.append(f"| `{caller}` | `{target}` | `{location}` |")

        return lines


def main():
    """Entry point"""
    project_root = Path(__file__).parent
    cache_dir = project_root / '.agent' / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Analizza call graph
    analyzer = CallGraphAnalyzer(project_root)

    try:
        call_graph = analyzer.analyze_project()

        # Salva JSON
        json_file = cache_dir / 'call_graph.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(call_graph, f, indent=2, ensure_ascii=False)

        logger.info(f"[OK] Call graph JSON saved to: {json_file}")

        # Genera markdown
        generator = MarkdownGenerator(call_graph)
        markdown = generator.generate()

        md_file = cache_dir / 'call_graph.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info(f"[OK] Call graph markdown saved to: {md_file}")

        # Stampa statistiche
        stats = call_graph['statistics']
        print("\n" + "=" * 80)
        print("CALL GRAPH ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\nStatistics:")
        print(f"  Total Classes:      {stats['total_classes']}")
        print(f"  Total Methods:      {stats['total_methods']}")
        print(f"  Total Functions:    {stats['total_functions']}")
        print(f"  Total Calls:        {stats['total_calls']}")
        print(f"\nOutput:")
        print(f"  JSON: {json_file}")
        print(f"  MD:   {md_file}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
