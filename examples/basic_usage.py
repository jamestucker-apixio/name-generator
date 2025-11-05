"""
Example usage of the name generator library.

This script demonstrates various ways to use the name generator
programmatically in your Python code.
"""

from name_generator.generator import NameGenerator, Ethnicity, Gender


def example_single_names():
    """Generate single first and last names."""
    print("=== Single Names Example ===\n")

    with NameGenerator() as generator:
        # Generate a Hispanic female first name
        first_name = generator.generate_first_name(
            ethnicity=Ethnicity.HISPANIC,
            gender=Gender.FEMALE
        )
        print(f"Hispanic female first name: {first_name.name}")
        print(f"Ethnic probabilities: {first_name.probabilities}\n")

        # Generate an Asian surname
        surname = generator.generate_last_name(ethnicity=Ethnicity.ASIAN)
        print(f"Asian surname: {surname.name}")
        print(f"Ethnic probabilities: {surname.probabilities}\n")


def example_full_names():
    """Generate full name combinations."""
    print("=== Full Names Example ===\n")

    with NameGenerator() as generator:
        # Generate 5 Black male full names
        for i in range(5):
            first, last = generator.generate_full_name(
                ethnicity=Ethnicity.BLACK,
                gender=Gender.MALE
            )
            print(f"{i+1}. {first.name} {last.name}")

        print()


def example_batch_generation():
    """Generate multiple names at once."""
    print("=== Batch Generation Example ===\n")

    with NameGenerator() as generator:
        # Generate 10 random names following US demographics
        names = generator.generate_batch(
            count=10,
            include_surnames=True
        )

        print("10 random names (US demographic distribution):")
        for i, name in enumerate(names, 1):
            full_name = name["full_name"]
            probs = name["ethnicity_probabilities"]
            dominant = max(probs, key=probs.get)
            print(f"{i:2d}. {full_name:30s} (likely {dominant})")

        print()


def example_specific_ethnicities():
    """Generate names for each ethnicity."""
    print("=== Ethnicity-Specific Names ===\n")

    ethnicities = [
        Ethnicity.WHITE,
        Ethnicity.BLACK,
        Ethnicity.HISPANIC,
        Ethnicity.ASIAN,
    ]

    with NameGenerator() as generator:
        for ethnicity in ethnicities:
            print(f"{ethnicity.value.capitalize()} names:")

            names = generator.generate_batch(
                count=3,
                ethnicity=ethnicity,
                include_surnames=True
            )

            for name in names:
                print(f"  - {name['full_name']}")

            print()


def example_gender_specific():
    """Generate gender-specific names."""
    print("=== Gender-Specific Names ===\n")

    with NameGenerator() as generator:
        # Female names
        print("Female names:")
        female_names = generator.generate_batch(
            count=5,
            gender=Gender.FEMALE,
            include_surnames=True
        )

        for name in female_names:
            print(f"  - {name['full_name']}")

        print()

        # Male names
        print("Male names:")
        male_names = generator.generate_batch(
            count=5,
            gender=Gender.MALE,
            include_surnames=True
        )

        for name in male_names:
            print(f"  - {name['full_name']}")

        print()


def example_first_names_only():
    """Generate first names without surnames."""
    print("=== First Names Only Example ===\n")

    with NameGenerator() as generator:
        names = generator.generate_batch(
            count=10,
            include_surnames=False
        )

        print("10 first names:")
        for i, name in enumerate(names, 1):
            first_name = name["first_name"]
            gender = name.get("gender", "?")
            print(f"{i:2d}. {first_name:20s} ({gender})")

        print()


def example_with_probabilities():
    """Show detailed ethnic probability information."""
    print("=== Names with Probability Details ===\n")

    with NameGenerator() as generator:
        names = generator.generate_batch(count=5, include_surnames=True)

        for i, name in enumerate(names, 1):
            print(f"{i}. {name['full_name']}")
            print(f"   Ethnic probabilities:")

            probs = name["ethnicity_probabilities"]
            for ethnicity in ["white", "black", "hispanic", "asian", "other"]:
                prob = probs[ethnicity]
                bar = "█" * int(prob * 50)  # Visual bar
                print(f"     {ethnicity:10s}: {prob:5.1%} {bar}")

            print()


def example_custom_distribution():
    """Use custom ethnic distribution instead of US demographics."""
    print("=== Custom Distribution Example ===\n")

    # Equal representation across all groups
    equal_distribution = {
        "white": 0.20,
        "black": 0.20,
        "hispanic": 0.20,
        "asian": 0.20,
        "other": 0.20
    }

    with NameGenerator() as generator:
        print("Generating 20 names with equal ethnic distribution:")

        names = generator.generate_batch(
            count=20,
            distribution=equal_distribution,
            include_surnames=True
        )

        # Count ethnicities
        ethnic_counts = {eth: 0 for eth in equal_distribution.keys()}

        for name in names:
            probs = name["ethnicity_probabilities"]
            dominant = max(probs, key=probs.get)
            ethnic_counts[dominant] += 1
            print(f"  {name['full_name']:30s} ({dominant})")

        print(f"\nDistribution: {ethnic_counts}")
        print()


def main():
    """Run all examples."""
    examples = [
        example_single_names,
        example_full_names,
        example_batch_generation,
        example_specific_ethnicities,
        example_gender_specific,
        example_first_names_only,
        example_with_probabilities,
        example_custom_distribution,
    ]

    print("Name Generator - Example Usage")
    print("=" * 60)
    print()

    for example in examples:
        try:
            example()
        except FileNotFoundError:
            print("Error: Database not found!")
            print("Run 'name-generator --setup' to download the dataset first.")
            break
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")

    print("=" * 60)
    print("Examples complete!")


if __name__ == "__main__":
    main()
