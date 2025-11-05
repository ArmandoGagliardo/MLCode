"""
Dataset Command
===============

Build and manage code datasets.

Examples:
    python -m presentation.cli dataset build --input data/collected --output data/dataset.json
    python -m presentation.cli dataset info --path data/dataset.json
    python -m presentation.cli dataset validate --path data/dataset.json
"""

import click
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@click.group()
def dataset():
    """Build and manage code datasets."""
    pass


@dataset.command()
@click.option('--input', '-i', type=click.Path(exists=True), required=True,
              help='Input directory with collected samples')
@click.option('--output', '-o', type=click.Path(), required=True,
              help='Output dataset file path')
@click.option('--format', type=click.Choice(['json', 'jsonl', 'parquet']),
              default='json', help='Output format')
@click.option('--split', type=float, default=0.8, help='Train/test split ratio')
@click.pass_context
def build(ctx, input, output, format, split):
    """
    Build a dataset from collected code samples.

    Combines multiple collection outputs into a single dataset file.

    Examples:

        Build JSON dataset:
        $ python -m presentation.cli dataset build --input data/collected --output data/dataset.json

        With custom split:
        $ python -m presentation.cli dataset build --input data/ --output data/train.json --split 0.9
    """
    verbose = ctx.obj.get('VERBOSE', False)

    click.echo("="*70)
    click.echo("BUILD DATASET")
    click.echo("="*70)
    click.echo()

    click.echo("Configuration:")
    click.echo(f"  Input: {input}")
    click.echo(f"  Output: {output}")
    click.echo(f"  Format: {format}")
    click.echo(f"  Split: {split:.0%} train / {1-split:.0%} test")
    click.echo()

    # Find all JSON files in input directory
    input_path = Path(input)
    if input_path.is_file():
        json_files = [input_path]
    else:
        json_files = list(input_path.rglob('*.json'))
        json_files = [f for f in json_files if not f.name.startswith('duplicates_cache')]

    if not json_files:
        click.secho(f"[ERROR] No JSON files found in {input}", fg='red')
        raise click.Abort()

    click.echo(f"Found {len(json_files)} collection files")
    click.echo()

    # Load and combine samples
    click.echo("Loading samples...")
    all_samples = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_samples.extend(data)
                elif isinstance(data, dict) and 'samples' in data:
                    all_samples.extend(data['samples'])
            click.echo(f"  [OK] {json_file.name}: {len(data)} samples")
        except Exception as e:
            click.echo(f"  [SKIP] {json_file.name}: {e}")

    if not all_samples:
        click.secho("[ERROR] No samples loaded", fg='red')
        raise click.Abort()

    click.echo()
    click.echo(f"Total samples: {len(all_samples)}")

    # Split train/test
    import random
    random.shuffle(all_samples)
    split_idx = int(len(all_samples) * split)
    train_samples = all_samples[:split_idx]
    test_samples = all_samples[split_idx:]

    click.echo(f"Train samples: {len(train_samples)}")
    click.echo(f"Test samples: {len(test_samples)}")
    click.echo()

    # Save dataset
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    click.echo(f"Saving to {output}...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'train': train_samples,
                'test': test_samples,
                'metadata': {
                    'total_samples': len(all_samples),
                    'train_samples': len(train_samples),
                    'test_samples': len(test_samples),
                    'split_ratio': split,
                    'source_files': len(json_files)
                }
            }, f, indent=2)

        click.secho("[OK] Dataset saved successfully!", fg='green', bold=True)
    except Exception as e:
        click.secho(f"[ERROR] Failed to save dataset: {e}", fg='red')
        raise click.Abort()

    click.echo()
    click.echo("="*70)


@dataset.command()
@click.option('--path', '-p', type=click.Path(exists=True), required=True,
              help='Path to dataset file')
@click.pass_context
def info(ctx, path):
    """
    Show information about a dataset.

    Examples:

        $ python -m presentation.cli dataset info --path data/dataset.json
    """
    click.echo("="*70)
    click.echo("DATASET INFORMATION")
    click.echo("="*70)
    click.echo()

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        click.echo(f"Dataset: {path}")
        click.echo()

        if isinstance(data, dict) and 'metadata' in data:
            metadata = data['metadata']
            click.echo("Metadata:")
            for key, value in metadata.items():
                click.echo(f"  {key}: {value}")
            click.echo()

            if 'train' in data and 'test' in data:
                click.echo("Splits:")
                click.echo(f"  Train: {len(data['train'])} samples")
                click.echo(f"  Test: {len(data['test'])} samples")

        elif isinstance(data, list):
            click.echo(f"Format: Simple list")
            click.echo(f"Total samples: {len(data)}")

            # Sample statistics
            if data:
                languages = {}
                for sample in data:
                    lang = sample.get('language', 'unknown')
                    languages[lang] = languages.get(lang, 0) + 1

                click.echo()
                click.echo("Languages:")
                for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                    click.echo(f"  {lang}: {count}")

    except Exception as e:
        click.secho(f"[ERROR] Failed to read dataset: {e}", fg='red')
        raise click.Abort()

    click.echo()
    click.echo("="*70)


@dataset.command()
@click.option('--path', '-p', type=click.Path(exists=True), required=True,
              help='Path to dataset file')
@click.pass_context
def validate(ctx, path):
    """
    Validate dataset integrity and quality.

    Examples:

        $ python -m presentation.cli dataset validate --path data/dataset.json
    """
    click.echo("="*70)
    click.echo("DATASET VALIDATION")
    click.echo("="*70)
    click.echo()

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        click.echo(f"Validating: {path}")
        click.echo()

        issues = []

        # Check format
        if isinstance(data, dict):
            if 'train' not in data or 'test' not in data:
                issues.append("Missing train/test splits")
            else:
                samples = data['train'] + data['test']
        elif isinstance(data, list):
            samples = data
        else:
            issues.append(f"Invalid format: {type(data)}")
            samples = []

        click.echo(f"Total samples: {len(samples)}")

        # Validate samples
        valid_samples = 0
        for i, sample in enumerate(samples):
            if not isinstance(sample, dict):
                issues.append(f"Sample {i}: Not a dictionary")
                continue

            # Check required fields
            if 'language' not in sample:
                issues.append(f"Sample {i}: Missing 'language' field")
            if 'input' not in sample and 'output' not in sample:
                issues.append(f"Sample {i}: Missing 'input' or 'output' field")

            valid_samples += 1

        click.echo(f"Valid samples: {valid_samples}/{len(samples)}")
        click.echo()

        if issues:
            click.secho(f"[WARNING] Found {len(issues)} issues:", fg='yellow')
            for issue in issues[:10]:  # Show first 10
                click.echo(f"  - {issue}")
            if len(issues) > 10:
                click.echo(f"  ... and {len(issues) - 10} more")
        else:
            click.secho("[OK] Dataset validation passed!", fg='green', bold=True)

    except Exception as e:
        click.secho(f"[ERROR] Validation failed: {e}", fg='red')
        raise click.Abort()

    click.echo()
    click.echo("="*70)
