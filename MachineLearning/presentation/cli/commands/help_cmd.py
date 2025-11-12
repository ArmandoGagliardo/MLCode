"""
Help Command
============

Comprehensive help system for ML Code Intelligence CLI.

Shows detailed information about all commands, options, and usage examples.
"""

import click


@click.command(name='help')
@click.argument('command', required=False)
@click.pass_context
def help_command(ctx, command):
    """
    Show detailed help for commands.

    Usage:
        python -m presentation.cli help          # Show all commands
        python -m presentation.cli help collect  # Help for collect command
        python -m presentation.cli help train    # Help for train command
    """
    if command:
        # Show help for specific command
        show_command_help(command)
    else:
        # Show general help
        show_general_help()


def show_general_help():
    """Show comprehensive help for all commands."""
    click.echo()
    click.echo("=" * 80)
    click.echo(" " * 20 + "ML CODE INTELLIGENCE SYSTEM - CLI HELP")
    click.echo("=" * 80)
    click.echo()

    # Header
    click.secho("VERSION:", fg='cyan', bold=True)
    click.echo("  v2.0.0 - Clean Architecture")
    click.echo()

    click.secho("DESCRIPTION:", fg='cyan', bold=True)
    click.echo("  A modular system for collecting, processing, and training ML models")
    click.echo("  on source code. Built with Clean Architecture and SOLID principles.")
    click.echo()

    # Usage
    click.secho("USAGE:", fg='cyan', bold=True)
    click.echo("  python -m presentation.cli [COMMAND] [OPTIONS]")
    click.echo("  python -m presentation.cli [COMMAND] --help")
    click.echo()

    # Available Commands
    click.secho("AVAILABLE COMMANDS:", fg='cyan', bold=True)
    click.echo()

    # Core Commands
    click.secho("  Core Commands:", fg='yellow')
    commands = [
        ("collect", "Collect code samples from GitHub repositories"),
        ("train", "Train ML models on code datasets"),
        ("dataset", "Build and manage code datasets"),
    ]

    for cmd, desc in commands:
        click.echo(f"    {cmd:<15} {desc}")
    click.echo()

    # System Commands
    click.secho("  System Commands:", fg='yellow')
    system_commands = [
        ("info", "Show system information and architecture"),
        ("health", "Check system health and component status"),
        ("help", "Show this help message"),
        ("version", "Show version information"),
    ]

    for cmd, desc in system_commands:
        click.echo(f"    {cmd:<15} {desc}")
    click.echo()

    # Quick Examples
    click.secho("QUICK START EXAMPLES:", fg='cyan', bold=True)
    click.echo()

    examples = [
        ("1. Collect Python code from GitHub",
         "python -m presentation.cli collect --language python --count 10"),

        ("2. Build dataset from collected samples",
         "python -m presentation.cli dataset build --input data/collected --output data/dataset.json"),

        ("3. Train model on dataset",
         "python -m presentation.cli train --dataset data/dataset.json --epochs 20"),

        ("4. Check system health",
         "python -m presentation.cli health"),

        ("5. Show detailed help for a command",
         "python -m presentation.cli help collect"),
    ]

    for title, cmd in examples:
        click.secho(f"  {title}:", fg='green')
        click.echo(f"    $ {cmd}")
        click.echo()

    # Global Options
    click.secho("GLOBAL OPTIONS:", fg='cyan', bold=True)
    click.echo("  -v, --verbose    Enable verbose output (debug mode)")
    click.echo("  -q, --quiet      Suppress output (errors only)")
    click.echo("  --version        Show version and exit")
    click.echo("  --help           Show this help message and exit")
    click.echo()

    # Architecture
    click.secho("ARCHITECTURE LAYERS:", fg='cyan', bold=True)
    click.echo("  Domain Layer         Business logic, models, interfaces")
    click.echo("  Application Layer    Use cases, services, orchestration")
    click.echo("  Infrastructure Layer Implementations (storage, parsers, GitHub API)")
    click.echo("  Presentation Layer   CLI, API, user interfaces (this layer)")
    click.echo()

    # Components
    click.secho("KEY COMPONENTS:", fg='cyan', bold=True)
    click.echo("  Parsers:           TreeSitter (Python, JavaScript, Java, Go, Rust, C++, TypeScript)")
    click.echo("  Quality Filter:    Heuristic-based code quality scoring")
    click.echo("  Deduplication:     AST-based duplicate detection")
    click.echo("  Storage:           Local filesystem, S3, DigitalOcean Spaces, MinIO")
    click.echo("  GitHub Integration: API v3 for repository discovery and cloning")
    click.echo("  Training:          PyTorch + HuggingFace Transformers")
    click.echo()

    # Documentation
    click.secho("DOCUMENTATION:", fg='cyan', bold=True)
    click.echo("  Getting Started:   docs/getting-started.md")
    click.echo("  Architecture:      docs/architecture.md")
    click.echo("  API Reference:     docs/api/")
    click.echo("  Examples:          examples/")
    click.echo()

    # Footer
    click.secho("MORE INFORMATION:", fg='cyan', bold=True)
    click.echo("  Command Help:      python -m presentation.cli COMMAND --help")
    click.echo("  Detailed Help:     python -m presentation.cli help COMMAND")
    click.echo("  System Info:       python -m presentation.cli info")
    click.echo("  Health Check:      python -m presentation.cli health")
    click.echo()
    click.echo("=" * 80)
    click.echo()


def show_command_help(command: str):
    """Show detailed help for a specific command."""
    command = command.lower()

    help_data = {
        'collect': {
            'name': 'collect',
            'description': 'Collect code samples from GitHub repositories',
            'usage': [
                'python -m presentation.cli collect --language LANGUAGE --count N',
                'python -m presentation.cli collect --url REPO_URL',
                'python -m presentation.cli collect --topic TOPIC --count N'
            ],
            'options': [
                ('-l, --language TEXT', 'Programming language to collect (python, javascript, java, etc.)'),
                ('-n, --count INTEGER', 'Number of repositories to process (default: 10)'),
                ('--min-stars INTEGER', 'Minimum star count for repositories'),
                ('--min-quality FLOAT', 'Minimum quality score 0-100 (default: 60.0)'),
                ('--url TEXT', 'Collect from specific repository URL'),
                ('--topic TEXT', 'Collect repositories by GitHub topic'),
                ('-o, --output PATH', 'Output directory for collected samples (default: data/collected)'),
                ('--cache / --no-cache', 'Enable/disable caching (default: enabled)'),
            ],
            'examples': [
                ('Collect 10 Python repositories',
                 'python -m presentation.cli collect --language python --count 10'),

                ('Collect high-quality JavaScript code',
                 'python -m presentation.cli collect --language javascript --count 20 --min-quality 80'),

                ('Collect from specific repository',
                 'python -m presentation.cli collect --url https://github.com/django/django'),

                ('Collect ML repositories',
                 'python -m presentation.cli collect --topic machine-learning --count 15'),

                ('Collect with custom output',
                 'python -m presentation.cli collect --language rust --output data/rust_samples'),
            ],
            'notes': [
                'Requires GitHub API token in environment (GITHUB_TOKEN) for rate limiting',
                'Collected samples are filtered by quality and deduplicated',
                'Supports 7 languages: Python, JavaScript, Java, Go, Rust, C++, TypeScript'
            ]
        },

        'train': {
            'name': 'train',
            'description': 'Train ML models on code datasets',
            'usage': [
                'python -m presentation.cli train --dataset PATH',
                'python -m presentation.cli train --dataset PATH --model MODEL --epochs N'
            ],
            'options': [
                ('-d, --dataset PATH', 'Path to dataset file or directory (required)'),
                ('-m, --model CHOICE', 'Model architecture: lstm, transformer, gpt (default: transformer)'),
                ('-e, --epochs INTEGER', 'Number of training epochs (default: 10)'),
                ('-b, --batch-size INTEGER', 'Batch size for training (default: 32)'),
                ('-lr, --learning-rate FLOAT', 'Learning rate (default: 0.001)'),
                ('-o, --output PATH', 'Output directory for trained model (default: models/)'),
                ('--resume PATH', 'Resume training from checkpoint'),
            ],
            'examples': [
                ('Basic training',
                 'python -m presentation.cli train --dataset data/dataset.json'),

                ('Advanced configuration',
                 'python -m presentation.cli train --dataset data/dataset.json --model transformer --epochs 20 --batch-size 64'),

                ('With custom learning rate',
                 'python -m presentation.cli train --dataset data/ --learning-rate 0.0001 --epochs 50'),

                ('Resume from checkpoint',
                 'python -m presentation.cli train --dataset data/dataset.json --resume models/checkpoint.pt'),
            ],
            'notes': [
                'Supports GPU acceleration (CUDA) if available',
                'Training progress is logged and can be monitored',
                'Models are saved with checkpoints every N steps'
            ]
        },

        'dataset': {
            'name': 'dataset',
            'description': 'Build and manage code datasets',
            'usage': [
                'python -m presentation.cli dataset build --input DIR --output FILE',
                'python -m presentation.cli dataset info --path FILE',
                'python -m presentation.cli dataset validate --path FILE'
            ],
            'subcommands': [
                ('build', 'Build dataset from collected samples'),
                ('info', 'Show dataset information and statistics'),
                ('validate', 'Validate dataset format and quality'),
                ('split', 'Split dataset into train/test sets'),
            ],
            'options': {
                'build': [
                    ('-i, --input PATH', 'Input directory with collected samples (required)'),
                    ('-o, --output PATH', 'Output dataset file path (required)'),
                    ('--format CHOICE', 'Output format: json, jsonl, parquet (default: json)'),
                    ('--split FLOAT', 'Train/test split ratio 0.0-1.0 (default: 0.8)'),
                ],
                'info': [
                    ('--path PATH', 'Path to dataset file (required)'),
                ],
                'validate': [
                    ('--path PATH', 'Path to dataset file (required)'),
                    ('--strict', 'Enable strict validation mode'),
                ]
            },
            'examples': [
                ('Build dataset',
                 'python -m presentation.cli dataset build --input data/collected --output data/dataset.json'),

                ('Build JSONL dataset',
                 'python -m presentation.cli dataset build --input data/ --output data/train.jsonl --format jsonl'),

                ('Show dataset info',
                 'python -m presentation.cli dataset info --path data/dataset.json'),

                ('Validate dataset',
                 'python -m presentation.cli dataset validate --path data/dataset.json --strict'),
            ],
            'notes': [
                'Supports multiple formats: JSON, JSONL, Parquet',
                'Automatically deduplicates samples during build',
                'Validation checks format, quality, and consistency'
            ]
        },

        'info': {
            'name': 'info',
            'description': 'Show system information and architecture overview',
            'usage': ['python -m presentation.cli info'],
            'options': [],
            'examples': [
                ('Show system info', 'python -m presentation.cli info'),
            ],
            'notes': [
                'Displays architecture layers and components',
                'Shows available commands and their purposes'
            ]
        },

        'health': {
            'name': 'health',
            'description': 'Check system health and component status',
            'usage': [
                'python -m presentation.cli health',
                'python -m presentation.cli health --component COMPONENT'
            ],
            'options': [
                ('--component CHOICE', 'Component to check: all, parsers, storage, github (default: all)'),
            ],
            'examples': [
                ('Check all components', 'python -m presentation.cli health'),
                ('Check parsers only', 'python -m presentation.cli health --component parsers'),
                ('Check storage', 'python -m presentation.cli health --component storage'),
            ],
            'notes': [
                'Verifies all components are properly configured',
                'Checks GitHub API rate limits',
                'Tests storage provider connectivity'
            ]
        },
    }

    if command not in help_data:
        click.secho(f"[ERROR] Unknown command: {command}", fg='red', bold=True)
        click.echo()
        click.echo("Available commands: collect, train, dataset, info, health, help")
        click.echo()
        click.echo("Use 'python -m presentation.cli help' to see all commands.")
        return

    data = help_data[command]

    # Print detailed help
    click.echo()
    click.echo("=" * 80)
    click.secho(f"  COMMAND: {data['name'].upper()}", fg='cyan', bold=True)
    click.echo("=" * 80)
    click.echo()

    click.secho("DESCRIPTION:", fg='yellow', bold=True)
    click.echo(f"  {data['description']}")
    click.echo()

    click.secho("USAGE:", fg='yellow', bold=True)
    for usage in data['usage']:
        click.echo(f"  {usage}")
    click.echo()

    if 'subcommands' in data:
        click.secho("SUBCOMMANDS:", fg='yellow', bold=True)
        for sub, desc in data['subcommands']:
            click.echo(f"  {sub:<15} {desc}")
        click.echo()

    if 'options' in data:
        if isinstance(data['options'], dict):
            # Subcommand options
            for subcmd, opts in data['options'].items():
                click.secho(f"OPTIONS ({subcmd}):", fg='yellow', bold=True)
                for opt, desc in opts:
                    click.echo(f"  {opt:<30} {desc}")
                click.echo()
        else:
            # Regular options
            click.secho("OPTIONS:", fg='yellow', bold=True)
            for opt, desc in data['options']:
                click.echo(f"  {opt:<30} {desc}")
            click.echo()

    click.secho("EXAMPLES:", fg='yellow', bold=True)
    for title, cmd in data['examples']:
        click.secho(f"  {title}:", fg='green')
        click.echo(f"    $ {cmd}")
        click.echo()

    if 'notes' in data:
        click.secho("NOTES:", fg='yellow', bold=True)
        for note in data['notes']:
            click.echo(f"  • {note}")
        click.echo()

    click.echo("=" * 80)
    click.echo()
