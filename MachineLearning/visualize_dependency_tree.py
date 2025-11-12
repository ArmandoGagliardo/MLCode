"""
Dependency Tree Visualizer
===========================

Legge il file dependency_tree.json e genera una visualizzazione markdown
dell'albero delle dipendenze.

Output: .agent/cache/dependency_tree.md
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict


class TreeVisualizer:
    """Visualizza l'albero delle dipendenze in formato markdown"""

    def __init__(self, tree_data: Dict[str, Any]):
        self.tree = tree_data
        self.visited: Set[str] = set()

    def generate_markdown(self) -> str:
        """Genera il markdown completo"""
        lines = []

        # Header
        lines.append("# Dependency Tree Analysis")
        lines.append("")
        lines.append(f"**Entry Point**: `{self.tree['entry_point']}`")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Statistics
        lines.extend(self._generate_statistics())
        lines.append("")

        # Architecture Layers
        lines.extend(self._generate_layers())
        lines.append("")

        # Dependency Tree
        lines.extend(self._generate_tree())
        lines.append("")

        # Import Analysis
        lines.extend(self._generate_import_analysis())
        lines.append("")

        # File Details
        lines.extend(self._generate_file_details())
        lines.append("")

        return "\n".join(lines)

    def _generate_statistics(self) -> List[str]:
        """Genera la sezione statistiche"""
        stats = self.tree['statistics']
        lines = []

        lines.append("## 📊 Statistics")
        lines.append("")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Files Analyzed | {stats['total_files_analyzed']} |")
        lines.append(f"| Total Imports | {stats['total_imports']} |")
        lines.append(f"| Total Functions | {stats['total_functions']} |")
        lines.append(f"| Total Classes | {stats['total_classes']} |")
        lines.append("")

        lines.append("### Import Types")
        lines.append("")
        lines.append("| Type | Count | Percentage |")
        lines.append("|------|-------|------------|")

        total_imports = stats['total_imports']
        for imp_type, count in sorted(stats['import_types'].items()):
            pct = (count / total_imports * 100) if total_imports > 0 else 0
            lines.append(f"| {imp_type.capitalize()} | {count} | {pct:.1f}% |")

        return lines

    def _generate_layers(self) -> List[str]:
        """Genera la sezione layer architetturali"""
        layers = self.tree['layers']
        lines = []

        lines.append("## 🏗️ Architecture Layers")
        lines.append("")
        lines.append("| Layer | Files | Functions | Classes |")
        lines.append("|-------|-------|-----------|---------|")

        for layer_name in ['presentation', 'application', 'infrastructure', 'domain', 'other']:
            if layer_name in layers and layers[layer_name]['files'] > 0:
                stats = layers[layer_name]
                lines.append(f"| {layer_name.capitalize()} | {stats['files']} | {stats['functions']} | {stats['classes']} |")

        return lines

    def _generate_tree(self) -> List[str]:
        """Genera l'albero delle dipendenze"""
        lines = []
        lines.append("## 🌲 Dependency Tree")
        lines.append("")
        lines.append("```")

        # Reset visited
        self.visited.clear()

        # Start from entry point
        entry = self.tree['entry_point'].replace('/', '\\')
        self._print_node(entry, lines, prefix="", is_last=True)

        lines.append("```")

        return lines

    def _print_node(self, file_path: str, lines: List[str], prefix: str = "", is_last: bool = True):
        """Stampa un nodo dell'albero ricorsivamente"""
        if file_path in self.visited:
            return

        self.visited.add(file_path)

        # Simboli per l'albero
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        # Nome file
        file_name = Path(file_path).name
        lines.append(f"{prefix}{connector}{file_name}")

        # Ottieni dipendenze
        graph_data = self.tree['dependency_graph'].get(file_path, {})
        dependencies = graph_data.get('dependencies', [])

        # Filtra solo dipendenze interne non ancora visitate
        internal_deps = [d for d in dependencies if d not in self.visited]

        # Stampa dipendenze
        for i, dep in enumerate(internal_deps):
            is_last_dep = (i == len(internal_deps) - 1)
            self._print_node(dep, lines, prefix + extension, is_last_dep)

    def _generate_import_analysis(self) -> List[str]:
        """Genera analisi dettagliata degli import"""
        lines = []
        lines.append("## 📦 Import Analysis")
        lines.append("")

        # Raggruppa import per tipo
        import_by_type = defaultdict(lambda: defaultdict(int))

        for file_path, data in self.tree['dependency_graph'].items():
            for imp in data['imports']:
                import_by_type[imp['type']][imp['module']] += 1

        # External packages più usati
        if 'external' in import_by_type:
            lines.append("### Most Used External Packages")
            lines.append("")
            lines.append("| Package | Usage Count |")
            lines.append("|---------|-------------|")

            external_sorted = sorted(import_by_type['external'].items(), key=lambda x: x[1], reverse=True)
            for pkg, count in external_sorted[:10]:
                lines.append(f"| `{pkg}` | {count} |")
            lines.append("")

        # Internal modules più usati
        if 'internal' in import_by_type:
            lines.append("### Most Used Internal Modules")
            lines.append("")
            lines.append("| Module | Usage Count |")
            lines.append("|--------|-------------|")

            internal_sorted = sorted(import_by_type['internal'].items(), key=lambda x: x[1], reverse=True)
            for mod, count in internal_sorted[:10]:
                lines.append(f"| `{mod}` | {count} |")
            lines.append("")

        return lines

    def _generate_file_details(self) -> List[str]:
        """Genera dettagli per ogni file"""
        lines = []
        lines.append("## 📄 File Details")
        lines.append("")

        # Ordina per layer
        files_by_layer = defaultdict(list)
        for file_path in self.tree['dependency_graph'].keys():
            if file_path.startswith('presentation\\'):
                files_by_layer['Presentation'].append(file_path)
            elif file_path.startswith('application\\'):
                files_by_layer['Application'].append(file_path)
            elif file_path.startswith('infrastructure\\'):
                files_by_layer['Infrastructure'].append(file_path)
            elif file_path.startswith('domain\\'):
                files_by_layer['Domain'].append(file_path)
            else:
                files_by_layer['Other'].append(file_path)

        # Stampa per layer
        for layer in ['Presentation', 'Application', 'Infrastructure', 'Domain', 'Other']:
            if layer not in files_by_layer:
                continue

            lines.append(f"### {layer} Layer")
            lines.append("")

            for file_path in sorted(files_by_layer[layer]):
                data = self.tree['dependency_graph'][file_path]

                # File header
                lines.append(f"#### `{file_path}`")
                lines.append("")

                # Statistiche file
                num_imports = len(data['imports'])
                num_functions = len(data['functions'])
                num_classes = len(data['classes'])
                num_deps = len(data['dependencies'])

                lines.append(f"- **Imports**: {num_imports}")
                lines.append(f"- **Functions**: {num_functions}")
                lines.append(f"- **Classes**: {num_classes}")
                lines.append(f"- **Dependencies**: {num_deps}")
                lines.append("")

                # Classes
                if data['classes']:
                    lines.append("**Classes**:")
                    lines.append("")
                    for cls in data['classes']:
                        bases = f" extends {', '.join(cls['bases'])}" if cls['bases'] else ""
                        lines.append(f"- `{cls['name']}`{bases}")
                        if cls['methods']:
                            method_names = [m['name'] for m in cls['methods'][:5]]
                            if len(cls['methods']) > 5:
                                method_names.append(f"... +{len(cls['methods']) - 5} more")
                            lines.append(f"  - Methods: {', '.join(method_names)}")
                    lines.append("")

                # Functions (solo prime 10)
                if data['functions']:
                    lines.append("**Functions**:")
                    lines.append("")
                    for func in data['functions'][:10]:
                        decorators = f" @{', @'.join(func['decorators'])}" if func['decorators'] else ""
                        async_marker = "async " if func['is_async'] else ""
                        lines.append(f"- `{async_marker}{func['name']}({', '.join(func['args'])})`{decorators}")
                    if len(data['functions']) > 10:
                        lines.append(f"- ... and {len(data['functions']) - 10} more functions")
                    lines.append("")

                # Import breakdown
                import_types = defaultdict(int)
                for imp in data['imports']:
                    import_types[imp['type']] += 1

                if import_types:
                    lines.append("**Import Breakdown**:")
                    lines.append("")
                    for imp_type, count in sorted(import_types.items()):
                        lines.append(f"- {imp_type.capitalize()}: {count}")
                    lines.append("")

                lines.append("---")
                lines.append("")

        return lines


def main():
    """Entry point"""
    project_root = Path(__file__).parent
    cache_dir = project_root / '.agent' / 'cache'

    # Leggi dependency tree JSON
    input_file = cache_dir / 'dependency_tree.json'
    if not input_file.exists():
        print(f"Error: {input_file} not found. Run build_dependency_tree.py first.")
        return 1

    with open(input_file, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)

    # Genera markdown
    visualizer = TreeVisualizer(tree_data)
    markdown = visualizer.generate_markdown()

    # Salva output
    output_file = cache_dir / 'dependency_tree.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"[OK] Dependency tree visualization saved to: {output_file}")
    print(f"  {len(markdown.splitlines())} lines generated")

    return 0


if __name__ == '__main__':
    sys.exit(main())
