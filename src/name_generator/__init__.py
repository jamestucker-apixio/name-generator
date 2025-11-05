"""
Ethnically diverse name generator CLI.
"""

import argparse
import json
import sys

from .generator import DEFAULT_ETHNIC_DISTRIBUTION, Ethnicity, Gender, NameGenerator


def parse_args(args=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate ethnically diverse names using voter file data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10 random full names
  name-generator --count 10

  # Generate 5 Hispanic female names
  name-generator --count 5 --ethnicity hispanic --gender female

  # Generate first names only
  name-generator --count 10 --first-only

  # Output as JSON
  name-generator --count 5 --format json

  # Setup database (first-time use)
  name-generator --setup
        """,
    )

    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Number of names to generate (default: 1)",
    )

    parser.add_argument(
        "-e",
        "--ethnicity",
        type=str,
        choices=["white", "black", "hispanic", "asian", "other", "any"],
        default="any",
        help="Target ethnicity (default: any, weighted by US demographics)",
    )

    parser.add_argument(
        "-g",
        "--gender",
        type=str,
        choices=["male", "female", "m", "f", "any"],
        default="any",
        help="Gender filter (default: any)",
    )

    parser.add_argument(
        "--first-only",
        action="store_true",
        help="Generate first names only (no surnames)",
    )

    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--min-probability",
        type=float,
        default=0.40,
        help="Minimum ethnic probability threshold (default: 0.40)",
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Download and setup the name database (required for first use)",
    )

    parser.add_argument("--db-path", type=str, help="Path to custom database file")

    return parser.parse_args(args)


def setup_database():
    """Run database setup."""
    from .data_loader import DataLoader

    print("Setting up name database...")
    print("Note: This will download data from Harvard Dataverse")
    loader = DataLoader()
    loader.setup_database()
    print("\nSetup complete! You can now generate names.")


def format_output(names: list, output_format: str, first_only: bool) -> str:
    """Format output based on user preference."""
    if output_format == "json":
        return json.dumps(names, indent=2)

    elif output_format == "csv":
        if not names:
            return ""

        if first_only:
            header = "first_name,gender,prob_white,prob_black,prob_hispanic,prob_asian,prob_other"
            lines = [header]
            for name in names:
                probs = name["ethnicity_probabilities"]
                lines.append(
                    f"{name['first_name']},{name.get('gender', '')},"
                    f"{probs['white']},{probs['black']},{probs['hispanic']},"
                    f"{probs['asian']},{probs['other']}"
                )
        else:
            header = "full_name,first_name,last_name,gender,prob_white,prob_black,prob_hispanic,prob_asian,prob_other"
            lines = [header]
            for name in names:
                probs = name["ethnicity_probabilities"]
                lines.append(
                    f"{name['full_name']},{name['first_name']},{name['last_name']},"
                    f"{name.get('gender', '')},{probs['white']},{probs['black']},"
                    f"{probs['hispanic']},{probs['asian']},{probs['other']}"
                )
        return "\n".join(lines)

    else:  # text format
        lines = []
        for name in names:
            if first_only:
                lines.append(name["first_name"])
            else:
                lines.append(name["full_name"])
        return "\n".join(lines)


def main(argv=None) -> None:
    """Main CLI entry point."""
    args = parse_args(argv)

    # Handle setup command
    if args.setup:
        setup_database()
        return

    # Map gender argument
    gender_map = {
        "male": Gender.MALE,
        "m": Gender.MALE,
        "female": Gender.FEMALE,
        "f": Gender.FEMALE,
        "any": Gender.ANY,
    }
    gender = gender_map.get(args.gender.lower(), Gender.ANY)

    # Map ethnicity argument
    ethnicity = Ethnicity.ANY if args.ethnicity == "any" else Ethnicity(args.ethnicity)

    try:
        # Initialize generator
        db_path = args.db_path if args.db_path else None
        with NameGenerator(db_path) as generator:
            # Generate names
            names = generator.generate_batch(
                count=args.count,
                ethnicity=ethnicity,
                gender=gender,
                include_surnames=not args.first_only,
                distribution=None,  # Use default US demographics
            )

            # Format and output
            output = format_output(names, args.format, args.first_only)
            print(output)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(
            "\nRun 'name-generator --setup' to download and setup the database.",
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
