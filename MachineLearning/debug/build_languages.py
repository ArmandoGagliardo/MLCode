from tree_sitter import Language

# Compila le grammatiche tree-sitter in un'unica libreria condivisa
Language.build_library(
    'build/my-languages.so',  # Su Windows sarà usato come .dll
    [
        'vendor/tree-sitter-cpp',
        'vendor/tree-sitter-python',
        'vendor/tree-sitter-java',
        'vendor/tree-sitter-javascript',
        'vendor/tree-sitter-php/php/',
        'vendor/tree-sitter-go',
        'vendor/tree-sitter-ruby',
        'vendor/tree-sitter-rust',
        'vendor/tree-sitter-typescript/typescript',
        'vendor/tree-sitter-html',
        'vendor/tree-sitter-css',
        'vendor/tree-sitter-json',
    ]
)

print("✅ Libreria Tree-sitter compilata: build/my-languages.so")