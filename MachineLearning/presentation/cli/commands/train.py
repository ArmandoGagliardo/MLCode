"""
Train Command
=============

Train ML models on collected code datasets.

Examples:
    python -m presentation.cli train --dataset data/dataset.json
    python -m presentation.cli train --dataset data/ --model transformer
"""

import click
import logging

logger = logging.getLogger(__name__)


@click.command()
@click.option('--dataset', '-d', type=click.Path(exists=True), required=True,
              help='Path to dataset file or directory')
@click.option('--model', '-m', type=click.Choice(['lstm', 'transformer', 'gpt']),
              default='transformer', help='Model architecture')
@click.option('--epochs', '-e', type=int, default=10, help='Number of training epochs')
@click.option('--batch-size', '-b', type=int, default=32, help='Batch size')
@click.option('--learning-rate', '-lr', type=float, default=0.001, help='Learning rate')
@click.option('--output', '-o', type=click.Path(), default='models/',
              help='Output directory for trained model')
@click.option('--resume', type=click.Path(exists=True), help='Resume from checkpoint')
@click.pass_context
def train(ctx, dataset, model, epochs, batch_size, learning_rate, output, resume):
    """
    Train ML models on code datasets.

    This command trains a model on collected code samples.
    Supports multiple architectures and configurations.

    Examples:

        Basic training:
        $ python -m presentation.cli train --dataset data/dataset.json

        Advanced configuration:
        $ python -m presentation.cli train --dataset data/ --model transformer \\
          --epochs 20 --batch-size 64 --learning-rate 0.0001
    """
    verbose = ctx.obj.get('VERBOSE', False)

    click.echo("="*70)
    click.echo("TRAIN ML MODEL")
    click.echo("="*70)
    click.echo()

    # Show configuration
    click.echo("Configuration:")
    click.echo(f"  Dataset: {dataset}")
    click.echo(f"  Model: {model}")
    click.echo(f"  Epochs: {epochs}")
    click.echo(f"  Batch size: {batch_size}")
    click.echo(f"  Learning rate: {learning_rate}")
    click.echo(f"  Output: {output}")
    if resume:
        click.echo(f"  Resume from: {resume}")
    click.echo()

    # Import use case
    try:
        from application.use_cases.train_model import TrainModelUseCase, TrainModelRequest
    except ImportError as e:
        click.secho(f"[ERROR] Failed to import TrainModelUseCase: {e}", fg='red')
        raise click.Abort()

    # Create use case
    use_case = TrainModelUseCase()

    # Create request
    train_request = TrainModelRequest(
        dataset_path=dataset,
        model_type=model,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        output_dir=output,
        resume_from=resume
    )

    click.echo("[1] Starting training...")
    click.echo()

    # Execute training
    try:
        response = use_case.execute(train_request)

        if response.success:
            click.secho("[OK] Training completed!", fg='green', bold=True)
            click.echo()
            click.echo("Results:")
            click.echo(f"  Model saved to: {response.model_path}")
            click.echo(f"  Epochs completed: {response.epochs_completed}/{epochs}")
            if response.final_accuracy is not None:
                click.echo(f"  Final accuracy: {response.final_accuracy:.4f}")
            if response.final_loss is not None:
                click.echo(f"  Final loss: {response.final_loss:.4f}")
            click.echo(f"  Training time: {response.training_time:.2f}s")

            if response.errors:
                click.echo()
                click.secho("Notes:", fg='yellow')
                for error in response.errors:
                    click.echo(f"  - {error}")
        else:
            click.secho("[FAIL] Training failed", fg='red', bold=True)
            if response.errors:
                click.echo()
                click.echo("Errors:")
                for error in response.errors:
                    click.echo(f"  - {error}")

    except KeyboardInterrupt:
        click.echo()
        click.secho("[INTERRUPTED] Training stopped by user", fg='yellow')
        raise click.Abort()
    except Exception as e:
        click.secho(f"[ERROR] Training failed: {e}", fg='red')
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

    click.echo()
    click.echo("="*70)
