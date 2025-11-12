"""
ML Code Intelligence System - CLI
==================================

Command-line interface for the ML Code Intelligence System.

Usage:
    python -m presentation.cli collect --language python --count 10
    python -m presentation.cli train --dataset data/dataset.json
    python -m presentation.cli dataset build --output data/

Architecture:
    This CLI follows Clean Architecture principles:
    - Presentation Layer (this file) → Application Layer (use cases) → Domain Layer
"""

import sys
import click
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from presentation.cli.commands import collect, train, dataset, help_cmd


@click.group()
@click.version_option(version="2.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
@click.pass_context
def cli(ctx, verbose, quiet):
    """
    ML Code Intelligence System - v2.0.0

    A modular system for collecting, processing, and training ML models on source code.

    Built with Clean Architecture and SOLID principles.
    """
    # Store options in context
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['QUIET'] = quiet

    # Configure logging based on verbosity
    import logging
    if quiet:
        logging.basicConfig(level=logging.ERROR)
    elif verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


# Register command groups
cli.add_command(collect.collect)
cli.add_command(train.train)
cli.add_command(dataset.dataset)
cli.add_command(help_cmd.help_command)


@cli.command()
def info():
    """Show system information and architecture overview."""
    click.echo("="*70)
    click.echo("ML Code Intelligence System v2.0.0")
    click.echo("="*70)
    click.echo()
    click.echo("Architecture: Clean Architecture + SOLID Principles")
    click.echo()
    click.echo("Layers:")
    click.echo("  - Domain:        Business logic, models, interfaces")
    click.echo("  - Application:   Use cases, services")
    click.echo("  - Infrastructure: Implementations (parsers, storage, etc.)")
    click.echo("  - Presentation:  CLI, API (this layer)")
    click.echo()
    click.echo("Components:")
    click.echo("  - Parsers:        TreeSitter (7 languages)")
    click.echo("  - Quality Filter: Heuristic-based scoring")
    click.echo("  - Deduplication:  AST-based")
    click.echo("  - GitHub:         API v3 integration")
    click.echo("  - Storage:        Local, S3, DigitalOcean")
    click.echo()
    click.echo("Commands:")
    click.echo("  collect  - Collect code from GitHub")
    click.echo("  train    - Train ML models")
    click.echo("  dataset  - Build and manage datasets")
    click.echo()
    click.echo("For help on a command: python -m presentation.cli COMMAND --help")
    click.echo("="*70)


@cli.command()
@click.option('--component', type=click.Choice(['all', 'parsers', 'storage', 'github']),
              default='all', help='Component to check')
def health(component):
    """Check system health and component status."""
    click.echo("Checking system health...")
    click.echo()

    checks_passed = 0
    checks_total = 0

    if component in ['all', 'parsers']:
        click.echo("[Parsers]")
        try:
            from infrastructure.parsers import TreeSitterParser
            parser = TreeSitterParser()
            langs = parser.get_supported_languages()
            click.echo(f"  [OK] TreeSitterParser: {len(langs)} languages")
            click.echo(f"       {', '.join(langs)}")
            checks_passed += 1
        except Exception as e:
            click.echo(f"  [FAIL] TreeSitterParser: {e}")
        checks_total += 1
        click.echo()

    if component in ['all', 'storage']:
        click.echo("[Storage]")
        try:
            from infrastructure.storage.providers import LocalProvider
            provider = LocalProvider({'base_path': 'data/storage'})
            click.echo(f"  [OK] LocalProvider: Ready")
            checks_passed += 1
        except Exception as e:
            click.echo(f"  [FAIL] LocalProvider: {e}")
        checks_total += 1
        click.echo()

    if component in ['all', 'github']:
        click.echo("[GitHub]")
        try:
            from infrastructure.github import GitHubFetcher
            fetcher = GitHubFetcher()
            limits = fetcher.get_rate_limit()
            click.echo(f"  [OK] GitHubFetcher: Ready")
            click.echo(f"       Rate limit: {limits.get('remaining', 0)}/{limits.get('limit', 0)}")
            checks_passed += 1
        except Exception as e:
            click.echo(f"  [FAIL] GitHubFetcher: {e}")
        checks_total += 1
        click.echo()

    # Summary
    click.echo("="*50)
    click.echo(f"Health Check: {checks_passed}/{checks_total} passed")
    if checks_passed == checks_total:
        click.secho("[OK] All systems operational", fg='green', bold=True)
    else:
        click.secho(f"[WARNING] {checks_total - checks_passed} components failed", fg='yellow', bold=True)
    click.echo("="*50)


def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
