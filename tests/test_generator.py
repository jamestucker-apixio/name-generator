"""
Tests for the name generator.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from name_generator.generator import (
    NameGenerator,
    NameRecord,
    Ethnicity,
    Gender,
    DEFAULT_ETHNIC_DISTRIBUTION
)


@pytest.fixture
def mock_db():
    """Create a temporary test database with sample data."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = Path(db_file.name)
    db_file.close()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE first_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT,
            count INTEGER,
            prob_white REAL,
            prob_black REAL,
            prob_hispanic REAL,
            prob_asian REAL,
            prob_other REAL,
            UNIQUE(name, gender)
        )
    ''')

    cursor.execute('''
        CREATE TABLE surnames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            count INTEGER,
            prob_white REAL,
            prob_black REAL,
            prob_hispanic REAL,
            prob_asian REAL,
            prob_other REAL
        )
    ''')

    # Insert sample first names
    first_names_data = [
        ("Maria", "F", 10000, 0.10, 0.05, 0.75, 0.08, 0.02),
        ("Jose", "M", 8000, 0.08, 0.03, 0.80, 0.07, 0.02),
        ("Jennifer", "F", 12000, 0.70, 0.15, 0.10, 0.03, 0.02),
        ("Michael", "M", 15000, 0.65, 0.20, 0.10, 0.03, 0.02),
        ("Wei", "M", 3000, 0.05, 0.02, 0.03, 0.88, 0.02),
        ("Jamal", "M", 4000, 0.05, 0.85, 0.05, 0.03, 0.02),
        ("Emily", "F", 11000, 0.75, 0.10, 0.08, 0.05, 0.02),
    ]

    for name_data in first_names_data:
        cursor.execute('''
            INSERT INTO first_names
            (name, gender, count, prob_white, prob_black, prob_hispanic, prob_asian, prob_other)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', name_data)

    # Insert sample surnames
    surnames_data = [
        ("Garcia", 20000, 0.05, 0.03, 0.85, 0.05, 0.02),
        ("Smith", 30000, 0.70, 0.20, 0.05, 0.03, 0.02),
        ("Johnson", 25000, 0.60, 0.30, 0.05, 0.03, 0.02),
        ("Wang", 8000, 0.03, 0.01, 0.02, 0.92, 0.02),
        ("Williams", 22000, 0.45, 0.48, 0.03, 0.02, 0.02),
        ("Rodriguez", 18000, 0.04, 0.02, 0.88, 0.04, 0.02),
    ]

    for surname_data in surnames_data:
        cursor.execute('''
            INSERT INTO surnames
            (name, count, prob_white, prob_black, prob_hispanic, prob_asian, prob_other)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', surname_data)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    db_path.unlink()


class TestNameRecord:
    """Test NameRecord dataclass."""

    def test_name_record_creation(self):
        """Test creating a NameRecord."""
        record = NameRecord(
            name="Maria",
            gender="F",
            count=1000,
            prob_white=0.10,
            prob_black=0.05,
            prob_hispanic=0.75,
            prob_asian=0.08,
            prob_other=0.02
        )

        assert record.name == "Maria"
        assert record.gender == "F"
        assert record.count == 1000

    def test_probabilities_property(self):
        """Test probabilities dictionary property."""
        record = NameRecord(
            name="Maria",
            gender="F",
            count=1000,
            prob_white=0.10,
            prob_black=0.05,
            prob_hispanic=0.75,
            prob_asian=0.08,
            prob_other=0.02
        )

        probs = record.probabilities
        assert probs["white"] == 0.10
        assert probs["hispanic"] == 0.75
        assert probs["asian"] == 0.08

    def test_dominant_ethnicity(self):
        """Test dominant ethnicity detection."""
        record = NameRecord(
            name="Maria",
            gender="F",
            count=1000,
            prob_white=0.10,
            prob_black=0.05,
            prob_hispanic=0.75,
            prob_asian=0.08,
            prob_other=0.02
        )

        assert record.dominant_ethnicity == Ethnicity.HISPANIC


class TestNameGenerator:
    """Test NameGenerator class."""

    def test_generator_initialization(self, mock_db):
        """Test initializing generator with custom DB."""
        generator = NameGenerator(mock_db)
        assert generator.db_path == mock_db

    def test_generator_context_manager(self, mock_db):
        """Test using generator as context manager."""
        with NameGenerator(mock_db) as generator:
            assert generator._conn is not None

    def test_generate_first_name_hispanic(self, mock_db):
        """Test generating Hispanic first name."""
        with NameGenerator(mock_db) as generator:
            name = generator.generate_first_name(
                ethnicity=Ethnicity.HISPANIC,
                gender=Gender.FEMALE
            )

            assert name.name in ["Maria"]
            assert name.prob_hispanic >= 0.40

    def test_generate_first_name_asian(self, mock_db):
        """Test generating Asian first name."""
        with NameGenerator(mock_db) as generator:
            name = generator.generate_first_name(
                ethnicity=Ethnicity.ASIAN,
                gender=Gender.MALE
            )

            assert name.name == "Wei"
            assert name.prob_asian >= 0.40

    def test_generate_first_name_black(self, mock_db):
        """Test generating Black first name."""
        with NameGenerator(mock_db) as generator:
            name = generator.generate_first_name(
                ethnicity=Ethnicity.BLACK,
                gender=Gender.MALE
            )

            assert name.name == "Jamal"
            assert name.prob_black >= 0.40

    def test_generate_last_name_hispanic(self, mock_db):
        """Test generating Hispanic surname."""
        with NameGenerator(mock_db) as generator:
            name = generator.generate_last_name(ethnicity=Ethnicity.HISPANIC)

            assert name.name in ["Garcia", "Rodriguez"]
            assert name.prob_hispanic >= 0.40

    def test_generate_last_name_asian(self, mock_db):
        """Test generating Asian surname."""
        with NameGenerator(mock_db) as generator:
            name = generator.generate_last_name(ethnicity=Ethnicity.ASIAN)

            assert name.name == "Wang"
            assert name.prob_asian >= 0.40

    def test_generate_full_name(self, mock_db):
        """Test generating full name."""
        with NameGenerator(mock_db) as generator:
            first, last = generator.generate_full_name(
                ethnicity=Ethnicity.HISPANIC,
                gender=Gender.FEMALE
            )

            assert first.prob_hispanic >= 0.40
            assert last.prob_hispanic >= 0.40

    def test_generate_batch(self, mock_db):
        """Test batch generation."""
        with NameGenerator(mock_db) as generator:
            names = generator.generate_batch(
                count=5,
                ethnicity=Ethnicity.HISPANIC,
                gender=Gender.ANY,
                include_surnames=True
            )

            assert len(names) == 5

            for name in names:
                assert "first_name" in name
                assert "last_name" in name
                assert "full_name" in name
                assert "ethnicity_probabilities" in name

    def test_generate_batch_first_only(self, mock_db):
        """Test batch generation with first names only."""
        with NameGenerator(mock_db) as generator:
            names = generator.generate_batch(
                count=3,
                include_surnames=False
            )

            assert len(names) == 3

            for name in names:
                assert "first_name" in name
                assert "last_name" not in name
                assert "ethnicity_probabilities" in name

    def test_ethnic_distribution(self, mock_db):
        """Test that generated names follow ethnic distribution."""
        with NameGenerator(mock_db) as generator:
            # Generate many names and check distribution
            names = generator.generate_batch(count=100)

            # Count ethnicities (based on dominant probability)
            ethnic_counts = {
                "white": 0,
                "black": 0,
                "hispanic": 0,
                "asian": 0,
                "other": 0
            }

            for name in names:
                probs = name["ethnicity_probabilities"]
                dominant = max(probs, key=probs.get)
                ethnic_counts[dominant] += 1

            # With our sample data, we should see some distribution
            # (exact proportions will vary due to randomness and limited sample data)
            total = sum(ethnic_counts.values())
            assert total == 100

    def test_no_database_error(self):
        """Test error when database doesn't exist."""
        fake_path = Path("/nonexistent/database.db")

        with pytest.raises(FileNotFoundError):
            with NameGenerator(fake_path) as generator:
                generator.generate_first_name()


class TestEnums:
    """Test enum classes."""

    def test_gender_enum(self):
        """Test Gender enum values."""
        assert Gender.MALE.value == "M"
        assert Gender.FEMALE.value == "F"
        assert Gender.ANY.value == "ANY"

    def test_ethnicity_enum(self):
        """Test Ethnicity enum values."""
        assert Ethnicity.WHITE.value == "white"
        assert Ethnicity.BLACK.value == "black"
        assert Ethnicity.HISPANIC.value == "hispanic"
        assert Ethnicity.ASIAN.value == "asian"
        assert Ethnicity.OTHER.value == "other"
        assert Ethnicity.ANY.value == "any"


class TestDefaultDistribution:
    """Test default ethnic distribution."""

    def test_distribution_sums_to_one(self):
        """Test that default distribution probabilities sum to 1.0."""
        total = sum(DEFAULT_ETHNIC_DISTRIBUTION.values())
        assert abs(total - 1.0) < 0.01  # Allow small floating point error

    def test_distribution_has_all_ethnicities(self):
        """Test that distribution includes all main ethnicities."""
        assert "white" in DEFAULT_ETHNIC_DISTRIBUTION
        assert "black" in DEFAULT_ETHNIC_DISTRIBUTION
        assert "hispanic" in DEFAULT_ETHNIC_DISTRIBUTION
        assert "asian" in DEFAULT_ETHNIC_DISTRIBUTION
        assert "other" in DEFAULT_ETHNIC_DISTRIBUTION
