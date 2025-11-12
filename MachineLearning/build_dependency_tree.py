"""
Dependency Tree Builder
=======================

Analizza le dipendenze del progetto partendo da presentation.cli
e costruisce un albero delle chiamate/importazioni.

Output: .agent/cache/dependency_tree.json
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analizza le dipendenze Python attraverso l'AST"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analyzed_files: Set[str] = set()
        self.dependency_graph: Dict[str, Dict[str, Any]] = {}
        self.import_map: Dict[str, str] = {}  # module_name -> file_path

    def analyze_project(self, entry_point: str) -> Dict[str, Any]:
        """
        Analizza il progetto partendo dall'entry point

        Args:
            entry_point: Percorso relativo al file entry point (es. "presentation/cli/main.py")

        Returns:
            Albero delle dipendenze
        """
        logger.info(f"Starting analysis from entry point: {entry_point}")

        # Build import map prima
        self._build_import_map()

        # Analizza entry point
        entry_file = self.project_root / entry_point
        if not entry_file.exists():
            raise FileNotFoundError(f"Entry point not found: {entry_file}")

        # Analizza ricorsivamente
        self._analyze_file(entry_file, depth=0)

        # Costruisci albero finale
        tree = self._build_tree(entry_point)

        return tree

    def _build_import_map(self):
        """Costruisce una mappa: nome_modulo -> percorso_file"""
        logger.info("Building import map...")

        py_files = list(self.project_root.glob("**/*.py"))
        logger.info(f"Found {len(py_files)} Python files")

        for py_file in py_files:
            # Ignora alcuni percorsi
            if any(x in str(py_file) for x in ['__pycache__', '.git', 'venv', 'env']):
                continue

            # Calcola il nome del modulo
            rel_path = py_file.relative_to(self.project_root)
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]

            # Rimuovi __init__
            if module_parts[-1] == '__init__':
                module_parts = module_parts[:-1]

            module_name = '.'.join(module_parts)
            self.import_map[module_name] = str(rel_path)

        logger.info(f"Built import map with {len(self.import_map)} modules")

    def _analyze_file(self, file_path: Path, depth: int = 0):
        """Analizza un singolo file Python"""
        rel_path = str(file_path.relative_to(self.project_root))

        # Evita cicli
        if rel_path in self.analyzed_files:
            return

        self.analyzed_files.add(rel_path)
        logger.info(f"{'  ' * depth}Analyzing: {rel_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content, filename=str(file_path))

            # Estrai informazioni
            imports = self._extract_imports(tree)
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)

            # Salva nel grafo
            self.dependency_graph[rel_path] = {
                'path': rel_path,
                'imports': imports,
                'functions': functions,
                'classes': classes,
                'dependencies': []
            }

            # Analizza ricorsivamente le dipendenze interne
            for imp in imports:
                if imp['type'] == 'internal':
                    dep_file = self._resolve_import(imp['module'])
                    if dep_file:
                        self.dependency_graph[rel_path]['dependencies'].append(str(dep_file))
                        # Analizza ricorsivamente (con limite di profondità)
                        if depth < 10:
                            dep_path = self.project_root / dep_file
                            if dep_path.exists():
                                self._analyze_file(dep_path, depth + 1)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {rel_path}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing {rel_path}: {e}")

    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Estrae tutti gli import da un AST"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': self._classify_import(alias.name),
                        'module': alias.name,
                        'alias': alias.asname,
                        'from': None
                    })

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'type': self._classify_import(module),
                        'module': module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'from': True,
                        'level': node.level
                    })

        return imports

    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Estrae tutte le funzioni da un AST"""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Solo funzioni top-level o metodi di classe
                functions.append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'is_async': False
                })
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'is_async': True
                })

        return functions

    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Estrae tutte le classi da un AST"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append({
                            'name': item.name,
                            'args': [arg.arg for arg in item.args.args],
                            'is_async': isinstance(item, ast.AsyncFunctionDef)
                        })

                classes.append({
                    'name': node.name,
                    'bases': [self._get_name(base) for base in node.bases],
                    'methods': methods,
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list]
                })

        return classes

    def _classify_import(self, module_name: str) -> str:
        """Classifica un import come internal, external o stdlib"""
        if not module_name:
            return 'relative'

        # Check se è un modulo interno
        parts = module_name.split('.')[0]
        if parts in ['domain', 'application', 'infrastructure', 'presentation']:
            return 'internal'

        # Check se è stdlib
        try:
            __import__(parts)
            import sys
            if parts in sys.stdlib_module_names:
                return 'stdlib'
        except:
            pass

        return 'external'

    def _resolve_import(self, module_name: str) -> str:
        """Risolve un nome di modulo al suo percorso file"""
        # Cerca nella import map
        if module_name in self.import_map:
            return self.import_map[module_name]

        # Prova con __init__
        init_module = f"{module_name}.__init__"
        if init_module in self.import_map:
            return self.import_map[init_module]

        # Prova a costruire il percorso
        possible_path = Path(module_name.replace('.', '/') + '.py')
        if (self.project_root / possible_path).exists():
            return str(possible_path)

        # Prova con __init__.py
        possible_init = Path(module_name.replace('.', '/') + '/__init__.py')
        if (self.project_root / possible_init).exists():
            return str(possible_init)

        return None

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Estrae il nome di un decorator"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_name(decorator.func)
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        return str(decorator)

    def _get_name(self, node: ast.AST) -> str:
        """Estrae il nome da un nodo AST"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return str(node)

    def _build_tree(self, entry_point: str) -> Dict[str, Any]:
        """Costruisce l'albero finale delle dipendenze"""
        logger.info("Building dependency tree...")

        # Statistiche
        total_files = len(self.dependency_graph)
        total_imports = sum(len(data['imports']) for data in self.dependency_graph.values())
        total_functions = sum(len(data['functions']) for data in self.dependency_graph.values())
        total_classes = sum(len(data['classes']) for data in self.dependency_graph.values())

        # Classifica imports per tipo
        import_types = defaultdict(int)
        for data in self.dependency_graph.values():
            for imp in data['imports']:
                import_types[imp['type']] += 1

        # Layer analysis
        layers = self._analyze_layers()

        tree = {
            'entry_point': entry_point,
            'statistics': {
                'total_files_analyzed': total_files,
                'total_imports': total_imports,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'import_types': dict(import_types)
            },
            'layers': layers,
            'dependency_graph': self.dependency_graph
        }

        return tree

    def _analyze_layers(self) -> Dict[str, Any]:
        """Analizza l'architettura a layer"""
        layers = {
            'presentation': [],
            'application': [],
            'infrastructure': [],
            'domain': [],
            'other': []
        }

        for file_path in self.dependency_graph.keys():
            if file_path.startswith('presentation/'):
                layers['presentation'].append(file_path)
            elif file_path.startswith('application/'):
                layers['application'].append(file_path)
            elif file_path.startswith('infrastructure/'):
                layers['infrastructure'].append(file_path)
            elif file_path.startswith('domain/'):
                layers['domain'].append(file_path)
            else:
                layers['other'].append(file_path)

        # Statistiche per layer
        layer_stats = {}
        for layer_name, files in layers.items():
            if not files:
                continue

            total_funcs = sum(len(self.dependency_graph[f]['functions']) for f in files)
            total_classes = sum(len(self.dependency_graph[f]['classes']) for f in files)

            layer_stats[layer_name] = {
                'files': len(files),
                'functions': total_funcs,
                'classes': total_classes,
                'file_list': files
            }

        return layer_stats


def main():
    """Entry point"""
    project_root = Path(__file__).parent

    # Crea directory cache se non esiste
    cache_dir = project_root / '.agent' / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Analizza dipendenze
    analyzer = DependencyAnalyzer(project_root)

    try:
        tree = analyzer.analyze_project('presentation/cli/main.py')

        # Salva risultato
        output_file = cache_dir / 'dependency_tree.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Dependency tree saved to: {output_file}")

        # Stampa statistiche
        print("\n" + "=" * 80)
        print("DEPENDENCY ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\nEntry Point: {tree['entry_point']}")
        print(f"\nStatistics:")
        print(f"  Files analyzed:    {tree['statistics']['total_files_analyzed']}")
        print(f"  Total imports:     {tree['statistics']['total_imports']}")
        print(f"  Total functions:   {tree['statistics']['total_functions']}")
        print(f"  Total classes:     {tree['statistics']['total_classes']}")
        print(f"\nImport Types:")
        for imp_type, count in tree['statistics']['import_types'].items():
            print(f"  {imp_type:12} {count:4}")
        print(f"\nArchitecture Layers:")
        for layer_name, stats in tree['layers'].items():
            print(f"  {layer_name:15} {stats['files']:3} files, {stats['functions']:4} functions, {stats['classes']:3} classes")
        print(f"\nOutput: {output_file}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
