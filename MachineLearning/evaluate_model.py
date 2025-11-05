"""
Model Evaluation Script

Comprehensive evaluation of trained models:
- Model validation checks
- Inference testing
- Performance benchmarks
- Quality assessment
- Report generation

Usage:
    python evaluate_model.py --model models/code_generation/
    python evaluate_model.py --model models/my_model/ --quick
    python evaluate_model.py --model models/my_model/ --output reports/
"""

import argparse
import sys
from pathlib import Path
import logging

# Add module path
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.validation import ModelValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(
        description='Evaluate trained ML model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full evaluation
  python evaluate_model.py --model models/code_generation/

  # Quick evaluation (skip benchmarks)
  python evaluate_model.py --model models/my_model/ --quick

  # Save report to specific location
  python evaluate_model.py --model models/my_model/ --output reports/

  # Custom test prompts
  python evaluate_model.py --model models/my_model/ --prompts prompts.txt
        """
    )

    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Path to model directory'
    )

    parser.add_argument(
        '--tokenizer',
        type=str,
        help='Path to tokenizer directory (default: same as model)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick evaluation (skip time-consuming checks)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='model_validation_reports',
        help='Output directory for reports (default: model_validation_reports)'
    )

    parser.add_argument(
        '--prompts',
        type=str,
        help='Path to file with test prompts (one per line)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate model path
    model_path = Path(args.model)
    if not model_path.exists():
        logger.error(f"Model path does not exist: {model_path}")
        return 1

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print("[*] MODEL EVALUATION")
    print("="*70)
    print(f"\nModel: {model_path}")
    print(f"Quick Mode: {'Yes' if args.quick else 'No'}")
    print(f"Output: {output_dir}")
    print()

    # Load test prompts if provided
    test_prompts = None
    if args.prompts:
        prompts_file = Path(args.prompts)
        if prompts_file.exists():
            with open(prompts_file, 'r') as f:
                test_prompts = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(test_prompts)} test prompts from {prompts_file}")
        else:
            logger.warning(f"Prompts file not found: {prompts_file}")

    # Initialize validator
    validator = ModelValidator(
        model_path=str(model_path),
        tokenizer_path=args.tokenizer
    )

    # Run validation
    try:
        result = validator.validate_all(quick=args.quick)

        # Print summary
        validator.print_summary()

        # Generate report filename
        model_name = model_path.name
        report_filename = f"validation_report_{model_name}.json"
        report_path = output_dir / report_filename

        # Save report
        result.save(str(report_path))

        print(f"\n[*] Validation Report: {report_path}")

        # Exit with appropriate code
        if result.passed:
            print("\n[SUCCESS] Model validation PASSED")
            return 0
        else:
            print("\n[FAIL] Model validation FAILED")
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors:
                print(f"  - {error}")

            if result.warnings:
                print(f"\nWarnings ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"  - {warning}")

            return 1

    except KeyboardInterrupt:
        print("\n\n[*] Evaluation interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
