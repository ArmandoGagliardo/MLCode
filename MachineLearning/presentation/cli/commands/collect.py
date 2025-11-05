"""
Collect Command
===============

Collect code samples from GitHub repositories.

Examples:
    python -m presentation.cli collect --language python --count 10
    python -m presentation.cli collect --language javascript --count 5 --min-stars 1000
    python -m presentation.cli collect --url https://github.com/django/django
"""

import click
import logging

logger = logging.getLogger(__name__)


@click.command()
@click.option('--language', '-l', type=str, help='Programming language to collect')
@click.option('--count', '-n', type=int, default=10, help='Number of repositories to process')
@click.option('--min-stars', type=int, help='Minimum star count for repositories')
@click.option('--min-quality', type=float, default=60.0, help='Minimum quality score (0-100)')
@click.option('--url', type=str, help='Collect from specific repository URL')
@click.option('--topic', type=str, help='Collect repositories by topic')
@click.option('--output', '-o', type=click.Path(), default='data/collected',
              help='Output directory for collected samples')
@click.option('--cache/--no-cache', default=True, help='Enable/disable caching')
@click.pass_context
def collect(ctx, language, count, min_stars, min_quality, url, topic, output, cache):
    """
    Collect code samples from GitHub repositories.

    This command fetches repositories from GitHub, parses the code,
    filters by quality, removes duplicates, and saves to storage.

    Examples:

        Collect Python code:
        $ python -m presentation.cli collect --language python --count 10

        Collect from specific repo:
        $ python -m presentation.cli collect --url https://github.com/django/django

        Collect by topic:
        $ python -m presentation.cli collect --topic machine-learning --count 20
    """
    verbose = ctx.obj.get('VERBOSE', False)

    click.echo("="*70)
    click.echo("COLLECT CODE FROM GITHUB")
    click.echo("="*70)
    click.echo()

    # Validate inputs
    if not any([language, url, topic]):
        click.secho("[ERROR] Must specify --language, --url, or --topic", fg='red', bold=True)
        raise click.Abort()

    # Import dependencies (lazy load)
    try:
        from infrastructure.parsers import TreeSitterParser
        from infrastructure.quality import HeuristicQualityFilter
        from infrastructure.duplicate import ASTDuplicateManager
        from infrastructure.github import GitHubFetcher
        from infrastructure.storage.providers import LocalProvider
        from application.services import ParserService, DataCollectionService
    except ImportError as e:
        click.secho(f"[ERROR] Failed to import dependencies: {e}", fg='red')
        raise click.Abort()

    # Initialize components
    click.echo("[1] Initializing components...")
    try:
        parser = TreeSitterParser()
        quality_filter = HeuristicQualityFilter(min_score=min_quality)
        dedup_manager = ASTDuplicateManager(
            cache_path=f'{output}/duplicates_cache.json' if cache else None
        )
        github_fetcher = GitHubFetcher()
        storage_provider = LocalProvider({'base_path': output})

        parser_service = ParserService(
            parser=parser,
            quality_filter=quality_filter,
            dedup_manager=dedup_manager
        )

        collection_service = DataCollectionService(
            repo_fetcher=github_fetcher,
            parser_service=parser_service,
            storage_provider=storage_provider
        )

        click.secho("    [OK] All components initialized", fg='green')
    except Exception as e:
        click.secho(f"    [FAIL] Initialization error: {e}", fg='red')
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

    click.echo()

    # Execute collection based on mode
    click.echo("[2] Starting collection...")
    try:
        if url:
            # Collect from specific URL
            click.echo(f"    Mode: Single repository")
            click.echo(f"    URL: {url}")
            result = collection_service.collect_from_url(url, min_quality=min_quality)

        elif topic:
            # Collect by topic
            click.echo(f"    Mode: By topic")
            click.echo(f"    Topic: {topic}")
            click.echo(f"    Count: {count}")
            result = collection_service.collect_from_topic(
                topic=topic,
                count=count,
                language=language,
                min_quality=min_quality
            )

        else:
            # Collect by language
            click.echo(f"    Mode: By language")
            click.echo(f"    Language: {language}")
            click.echo(f"    Count: {count}")
            click.echo(f"    Min stars: {min_stars or 'any'}")
            result = collection_service.collect_from_language(
                language=language,
                count=count,
                min_stars=min_stars,
                min_quality=min_quality
            )

        click.echo()

        # Display results
        if result.success:
            click.secho("[OK] Collection completed successfully!", fg='green', bold=True)
            click.echo()
            click.echo("Results:")
            click.echo(f"  Repositories processed: {result.repos_processed}/{result.repos_requested}")
            click.echo(f"  Total samples collected: {result.total_samples}")
            click.echo(f"  Output directory: {output}")

            if result.errors:
                click.echo()
                click.secho(f"  Warnings: {len(result.errors)} errors occurred", fg='yellow')
                if verbose:
                    for error in result.errors[:5]:
                        click.echo(f"    - {error}")

        else:
            click.secho("[FAIL] Collection failed", fg='red', bold=True)
            if result.errors:
                click.echo()
                click.echo("Errors:")
                for error in result.errors:
                    click.echo(f"  - {error}")

    except KeyboardInterrupt:
        click.echo()
        click.secho("[INTERRUPTED] Collection stopped by user", fg='yellow')
        raise click.Abort()
    except Exception as e:
        click.secho(f"[ERROR] Collection failed: {e}", fg='red')
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

    click.echo()
    click.echo("="*70)
