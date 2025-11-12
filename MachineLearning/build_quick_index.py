"""
Quick Index Builder for Agent Memory
=====================================

Crea indici ottimizzati per lookup rapido nella cache dell'agent.
Permette di trovare istantaneamente classi, metodi, funzioni senza rileggere file.

Output: .agent/cache/quick_index.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QuickIndexBuilder:
    """Costruisce indici per ricerca rapida"""

    def __init__(self, call_graph_file: Path):
        self.call_graph_file = call_graph_file
        self.index = {
            'by_name': {},           # class_name -> full info
            'by_method': {},         # method_name -> [classes that have it]
            'by_file': {},           # file_path -> [classes in it]
            'by_layer': {},          # layer -> [classes]
            'by_pattern': {},        # pattern -> [classes]
            'by_interface': {},      # interface -> [implementations]
            'by_keyword': {},        # keyword -> [classes/methods]
            'entry_points': [],      # Public API entry points
            'use_cases': {},         # use_case -> implementation
            'services': {},          # service_name -> class
            'quick_lookup': {}       # Fast lookup table
        }

    def build(self) -> Dict[str, Any]:
        """Costruisce tutti gli indici"""
        logger.info("Building quick index from call graph...")

        # Carica call graph
        with open(self.call_graph_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Build indici
        self._index_classes(data.get('classes', {}))
        self._index_functions(data.get('functions', {}))
        self._index_patterns(data.get('design_patterns', {}))
        self._index_interfaces(data.get('interfaces', {}), data.get('implementations', {}))
        self._build_keyword_index()
        self._identify_entry_points(data.get('classes', {}))
        self._identify_use_cases(data.get('classes', {}))
        self._build_quick_lookup()

        return self.index

    def _index_classes(self, classes: Dict):
        """Indicizza classi per nome, file, layer"""
        logger.info(f"Indexing {len(classes)} classes...")

        for full_name, cls_data in classes.items():
            class_name = cls_data['name']
            file_path = cls_data['file']
            layer = self._get_layer(file_path)

            # By name (case-insensitive)
            self.index['by_name'][class_name.lower()] = {
                'full_name': full_name,
                'name': class_name,
                'file': file_path,
                'line': cls_data['line'],
                'layer': layer,
                'type': 'class',
                'methods': [m['name'] for m in cls_data.get('methods', [])],
                'bases': cls_data.get('bases', []),
                'docstring': cls_data.get('docstring', ''),
                'is_interface': 'interfaces' in file_path,
                'is_abstract': cls_data.get('is_abstract', False)
            }

            # By file
            if file_path not in self.index['by_file']:
                self.index['by_file'][file_path] = []
            self.index['by_file'][file_path].append(class_name)

            # By layer
            if layer not in self.index['by_layer']:
                self.index['by_layer'][layer] = []
            self.index['by_layer'][layer].append(class_name)

            # By method name
            for method in cls_data.get('methods', []):
                method_name = method['name'].lower()
                if method_name not in self.index['by_method']:
                    self.index['by_method'][method_name] = []
                self.index['by_method'][method_name].append({
                    'class': class_name,
                    'full_name': full_name,
                    'file': file_path,
                    'line': method['line'],
                    'params': method.get('params', []),
                    'return_type': method.get('return_type'),
                    'docstring': method.get('docstring', '')
                })

    def _index_functions(self, functions: Dict):
        """Indicizza funzioni standalone"""
        logger.info(f"Indexing {len(functions)} functions...")

        for full_name, func_data in functions.items():
            func_name = func_data['name']
            file_path = func_data['file']

            self.index['by_name'][func_name.lower()] = {
                'full_name': full_name,
                'name': func_name,
                'file': file_path,
                'line': func_data['line'],
                'layer': self._get_layer(file_path),
                'type': 'function',
                'params': func_data.get('params', []),
                'return_type': func_data.get('return_type'),
                'docstring': func_data.get('docstring', '')
            }

    def _index_patterns(self, patterns: Dict):
        """Indicizza design patterns"""
        logger.info("Indexing design patterns...")

        for pattern_name, instances in patterns.items():
            if not instances:
                continue

            self.index['by_pattern'][pattern_name] = []
            for instance in instances:
                class_full_name = instance.get('class', '')
                if '::' in class_full_name:
                    class_name = class_full_name.split('::')[-1]
                    self.index['by_pattern'][pattern_name].append({
                        'class': class_name,
                        'full_name': class_full_name,
                        'file': instance.get('file', ''),
                        'confidence': instance.get('confidence', 'medium')
                    })

    def _index_interfaces(self, interfaces: Dict, implementations: Dict):
        """Indicizza interfacce e implementazioni"""
        logger.info(f"Indexing {len(interfaces)} interfaces...")

        for interface_full_name, interface_data in interfaces.items():
            interface_name = interface_data['name']

            # Trova implementazioni
            impls = implementations.get(interface_full_name, [])
            impl_names = [impl.split('::')[-1] for impl in impls]

            self.index['by_interface'][interface_name] = {
                'full_name': interface_full_name,
                'file': interface_data['file'],
                'implementations': impl_names,
                'implementation_count': len(impl_names),
                'methods': [m['name'] for m in interface_data.get('methods', [])]
            }

    def _build_keyword_index(self):
        """Indicizza per keyword (per ricerca full-text)"""
        logger.info("Building keyword index...")

        for name_lower, info in self.index['by_name'].items():
            # Estrai keywords dal nome
            keywords = self._extract_keywords(info['name'])

            # Aggiungi keywords dal docstring
            if info.get('docstring'):
                keywords.extend(self._extract_keywords(info['docstring']))

            # Indicizza
            for keyword in set(keywords):
                if keyword not in self.index['by_keyword']:
                    self.index['by_keyword'][keyword] = []
                self.index['by_keyword'][keyword].append({
                    'name': info['name'],
                    'type': info['type'],
                    'file': info['file'],
                    'layer': info['layer']
                })

    def _identify_entry_points(self, classes: Dict):
        """Identifica entry points pubblici (CLI commands, API endpoints)"""
        logger.info("Identifying entry points...")

        for full_name, cls_data in classes.items():
            file_path = cls_data['file']

            # CLI commands
            if 'presentation\\cli\\commands' in file_path:
                self.index['entry_points'].append({
                    'type': 'cli_command',
                    'name': cls_data['name'],
                    'file': file_path,
                    'purpose': cls_data.get('docstring', '').split('\n')[0] if cls_data.get('docstring') else ''
                })

    def _identify_use_cases(self, classes: Dict):
        """Identifica use cases nell'application layer"""
        logger.info("Identifying use cases...")

        for full_name, cls_data in classes.items():
            if 'application\\use_cases' in cls_data['file']:
                use_case_name = cls_data['name']
                self.index['use_cases'][use_case_name] = {
                    'full_name': full_name,
                    'file': cls_data['file'],
                    'line': cls_data['line'],
                    'methods': [m['name'] for m in cls_data.get('methods', [])],
                    'docstring': cls_data.get('docstring', '')
                }

            elif 'application\\services' in cls_data['file']:
                service_name = cls_data['name']
                self.index['services'][service_name] = {
                    'full_name': full_name,
                    'file': cls_data['file'],
                    'line': cls_data['line'],
                    'methods': [m['name'] for m in cls_data.get('methods', [])],
                    'docstring': cls_data.get('docstring', '')
                }

    def _build_quick_lookup(self):
        """Costruisce tabella di lookup ultra-rapido"""
        logger.info("Building quick lookup table...")

        # Shortcuts per concetti comuni
        self.index['quick_lookup'] = {
            # Storage
            'storage': self._find_classes_matching('storage'),
            'storage_providers': self._find_classes_in_path('infrastructure\\storage\\providers'),

            # Parsing
            'parsers': self._find_classes_matching('parser'),

            # Training
            'training': self._find_classes_in_path('infrastructure\\training'),

            # Inference
            'inference': self._find_classes_in_path('infrastructure\\inference'),

            # Services
            'services': list(self.index['services'].keys()),

            # Use Cases
            'use_cases': list(self.index['use_cases'].keys()),

            # Interfaces
            'interfaces': list(self.index['by_interface'].keys()),

            # CLI
            'cli_commands': [ep['name'] for ep in self.index['entry_points'] if ep['type'] == 'cli_command']
        }

    def _get_layer(self, file_path: str) -> str:
        """Estrae il layer dal percorso file"""
        if file_path.startswith('domain'):
            return 'domain'
        elif file_path.startswith('application'):
            return 'application'
        elif file_path.startswith('infrastructure'):
            return 'infrastructure'
        elif file_path.startswith('presentation'):
            return 'presentation'
        return 'other'

    def _extract_keywords(self, text: str) -> List[str]:
        """Estrae keywords da un testo"""
        import re

        # Split su camelCase e snake_case
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', text)
        words.extend(text.lower().split('_'))
        words.extend(text.lower().split())

        # Filtra parole corte e comuni
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [w.lower() for w in words if len(w) > 2 and w.lower() not in stop_words]

        return keywords

    def _find_classes_matching(self, keyword: str) -> List[str]:
        """Trova classi che contengono keyword nel nome"""
        matches = []
        for name, info in self.index['by_name'].items():
            if keyword.lower() in name.lower() and info['type'] == 'class':
                matches.append(info['name'])
        return matches

    def _find_classes_in_path(self, path: str) -> List[str]:
        """Trova classi in un path specifico"""
        matches = []
        for file_path, classes in self.index['by_file'].items():
            if path in file_path:
                matches.extend(classes)
        return matches


def main():
    """Entry point"""
    project_root = Path(__file__).parent
    cache_dir = project_root / '.agent' / 'cache'

    # Verifica che call_graph_v2.json esista
    call_graph_file = cache_dir / 'call_graph_v2.json'
    if not call_graph_file.exists():
        # Fallback a versione base
        call_graph_file = cache_dir / 'call_graph.json'
        if not call_graph_file.exists():
            logger.error("No call graph found. Run build_call_graph_v2.py first.")
            return 1

    # Build index
    builder = QuickIndexBuilder(call_graph_file)

    try:
        index = builder.build()

        # Salva index
        output_file = cache_dir / 'quick_index.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        logger.info(f"[OK] Quick index saved to: {output_file}")

        # Statistiche
        print("\n" + "=" * 80)
        print("QUICK INDEX BUILD COMPLETE")
        print("=" * 80)
        print(f"\nIndex Statistics:")
        print(f"  Classes/Functions indexed:    {len(index['by_name'])}")
        print(f"  Methods indexed:              {len(index['by_method'])}")
        print(f"  Files indexed:                {len(index['by_file'])}")
        print(f"  Keywords indexed:             {len(index['by_keyword'])}")
        print(f"  Interfaces:                   {len(index['by_interface'])}")
        print(f"  Use Cases:                    {len(index['use_cases'])}")
        print(f"  Services:                     {len(index['services'])}")
        print(f"  Entry Points:                 {len(index['entry_points'])}")
        print(f"\nLayers:")
        for layer, classes in index['by_layer'].items():
            print(f"  {layer:15} {len(classes):3} classes")
        print(f"\nDesign Patterns:")
        for pattern, instances in index['by_pattern'].items():
            print(f"  {pattern:20} {len(instances):3} instances")
        print(f"\nOutput: {output_file}")
        print("=" * 80)

        # Esempi di lookup
        print("\n[EXAMPLES] Quick Lookup:")
        print(f"  Storage providers:  {len(index['quick_lookup']['storage_providers'])}")
        print(f"  Parsers:            {len(index['quick_lookup']['parsers'])}")
        print(f"  CLI commands:       {len(index['quick_lookup']['cli_commands'])}")
        print(f"  Interfaces:         {len(index['quick_lookup']['interfaces'])}")

    except Exception as e:
        logger.error(f"Index build failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
