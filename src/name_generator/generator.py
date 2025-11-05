"""
Core name generation logic with ethnic diversity support.
"""

import random
import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# US demographic proportions (2024 estimates)
DEFAULT_ETHNIC_DISTRIBUTION = {
    "white": 0.60,
    "hispanic": 0.18,
    "black": 0.13,
    "asian": 0.06,
    "other": 0.03,
}


class Gender(Enum):
    """Gender options for name generation."""

    MALE = "M"
    FEMALE = "F"
    ANY = "ANY"


class Ethnicity(Enum):
    """Ethnic categories based on Census classifications."""

    WHITE = "white"
    BLACK = "black"
    HISPANIC = "hispanic"
    ASIAN = "asian"
    OTHER = "other"
    ANY = "any"


@dataclass
class NameRecord:
    """Represents a name with ethnic probability distribution."""

    name: str
    gender: Optional[str]
    count: int
    prob_white: float
    prob_black: float
    prob_hispanic: float
    prob_asian: float
    prob_other: float

    @property
    def probabilities(self) -> Dict[str, float]:
        """Get ethnic probabilities as a dictionary."""
        return {
            "white": self.prob_white,
            "black": self.prob_black,
            "hispanic": self.prob_hispanic,
            "asian": self.prob_asian,
            "other": self.prob_other,
        }

    @property
    def dominant_ethnicity(self) -> Ethnicity:
        """Get the most likely ethnicity for this name."""
        probs = self.probabilities
        dominant = max(probs, key=probs.get)
        return Ethnicity(dominant)


class NameGenerator:
    """Generates ethnically diverse names using voter file data."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the name generator.

        Args:
            db_path: Path to the SQLite database. If None, uses default location.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "names.db"

        self.db_path = db_path
        self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Get database connection (lazy initialization)."""
        if self._conn is None:
            if not self.db_path.exists():
                raise FileNotFoundError(
                    f"Database not found at {self.db_path}. "
                    "Run 'python -m name_generator.data_loader' to download and set up data."
                )
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _select_ethnicity(
        self,
        ethnicity: Optional[Ethnicity] = None,
        distribution: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Select an ethnicity based on distribution.

        Args:
            ethnicity: Specific ethnicity to use, or None for weighted random
            distribution: Custom ethnic distribution, or None for US demographics

        Returns:
            Selected ethnicity as string
        """
        if ethnicity and ethnicity != Ethnicity.ANY:
            return ethnicity.value

        if distribution is None:
            distribution = DEFAULT_ETHNIC_DISTRIBUTION

        # Weighted random selection
        ethnicities = list(distribution.keys())
        weights = list(distribution.values())
        return random.choices(ethnicities, weights=weights, k=1)[0]

    def _fetch_names(
        self,
        table: str,
        ethnicity: str,
        gender: Optional[Gender] = None,
        min_probability: float = 0.40,
    ) -> List[NameRecord]:
        """
        Fetch names from database matching criteria.

        Args:
            table: Table name ('first_names' or 'surnames')
            ethnicity: Target ethnicity
            gender: Gender filter (for first names only)
            min_probability: Minimum ethnic probability threshold

        Returns:
            List of matching NameRecord objects
        """
        query = f"SELECT * FROM {table} WHERE prob_{ethnicity} >= ?"
        params = [min_probability]

        if gender and gender != Gender.ANY and table == "first_names":
            query += " AND gender = ?"
            params.append(gender.value)

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            # Check if gender column exists (only in first_names table)
            try:
                gender_value = row["gender"] if row["gender"] else None
            except IndexError:
                gender_value = None

            results.append(
                NameRecord(
                    name=row["name"],
                    gender=gender_value,
                    count=row["count"],
                    prob_white=row["prob_white"],
                    prob_black=row["prob_black"],
                    prob_hispanic=row["prob_hispanic"],
                    prob_asian=row["prob_asian"],
                    prob_other=row["prob_other"],
                )
            )

        return results

    def _weighted_select(self, names: List[NameRecord], ethnicity: str) -> NameRecord:
        """
        Select a name using weighted random selection based on ethnic probability.

        Args:
            names: List of candidate names
            ethnicity: Target ethnicity for weighting

        Returns:
            Selected NameRecord
        """
        if not names:
            raise ValueError("No names available for selection")

        # Weight by both ethnic probability and count
        weights = [
            getattr(name, f"prob_{ethnicity}") * (1 + (name.count / 100000))
            for name in names
        ]

        return random.choices(names, weights=weights, k=1)[0]

    def generate_first_name(
        self,
        ethnicity: Optional[Ethnicity] = None,
        gender: Optional[Gender] = None,
        distribution: Optional[Dict[str, float]] = None,
        min_probability: float = 0.40,
    ) -> NameRecord:
        """
        Generate a first name.

        Args:
            ethnicity: Target ethnicity, or None for weighted random selection
            gender: Gender preference (MALE, FEMALE, or ANY)
            distribution: Custom ethnic distribution
            min_probability: Minimum ethnic probability threshold

        Returns:
            NameRecord for the generated first name
        """
        target_ethnicity = self._select_ethnicity(ethnicity, distribution)
        gender = gender or Gender.ANY

        names = self._fetch_names(
            "first_names", target_ethnicity, gender, min_probability
        )

        # If no names meet threshold, lower it
        if not names and min_probability > 0.20:
            names = self._fetch_names("first_names", target_ethnicity, gender, 0.20)

        if not names:
            raise ValueError(
                f"No first names found for ethnicity={target_ethnicity}, "
                f"gender={gender.value}"
            )

        return self._weighted_select(names, target_ethnicity)

    def generate_last_name(
        self,
        ethnicity: Optional[Ethnicity] = None,
        distribution: Optional[Dict[str, float]] = None,
        min_probability: float = 0.40,
    ) -> NameRecord:
        """
        Generate a surname.

        Args:
            ethnicity: Target ethnicity, or None for weighted random selection
            distribution: Custom ethnic distribution
            min_probability: Minimum ethnic probability threshold

        Returns:
            NameRecord for the generated surname
        """
        target_ethnicity = self._select_ethnicity(ethnicity, distribution)

        names = self._fetch_names(
            "surnames", target_ethnicity, min_probability=min_probability
        )

        # If no names meet threshold, lower it
        if not names and min_probability > 0.20:
            names = self._fetch_names(
                "surnames", target_ethnicity, min_probability=0.20
            )

        if not names:
            raise ValueError(f"No surnames found for ethnicity={target_ethnicity}")

        return self._weighted_select(names, target_ethnicity)

    def generate_full_name(
        self,
        ethnicity: Optional[Ethnicity] = None,
        gender: Optional[Gender] = None,
        distribution: Optional[Dict[str, float]] = None,
        min_probability: float = 0.40,
    ) -> Tuple[NameRecord, NameRecord]:
        """
        Generate a culturally compatible full name (first + last).

        Args:
            ethnicity: Target ethnicity, or None for weighted random selection
            gender: Gender preference
            distribution: Custom ethnic distribution
            min_probability: Minimum ethnic probability threshold

        Returns:
            Tuple of (first_name_record, last_name_record)
        """
        target_ethnicity = self._select_ethnicity(ethnicity, distribution)

        # Generate first and last name with same ethnic preference
        first_name = self.generate_first_name(
            Ethnicity(target_ethnicity), gender, distribution, min_probability
        )

        last_name = self.generate_last_name(
            Ethnicity(target_ethnicity), distribution, min_probability
        )

        return first_name, last_name

    def generate_batch(
        self,
        count: int = 10,
        ethnicity: Optional[Ethnicity] = None,
        gender: Optional[Gender] = None,
        include_surnames: bool = True,
        distribution: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, str]]:
        """
        Generate multiple names.

        Args:
            count: Number of names to generate
            ethnicity: Target ethnicity filter
            gender: Gender filter
            include_surnames: Whether to include surnames
            distribution: Custom ethnic distribution

        Returns:
            List of dictionaries with name data
        """
        results = []

        for _ in range(count):
            if include_surnames:
                first, last = self.generate_full_name(ethnicity, gender, distribution)
                results.append(
                    {
                        "first_name": first.name,
                        "last_name": last.name,
                        "full_name": f"{first.name} {last.name}",
                        "gender": first.gender,
                        "ethnicity_probabilities": {
                            "white": round((first.prob_white + last.prob_white) / 2, 3),
                            "black": round((first.prob_black + last.prob_black) / 2, 3),
                            "hispanic": round(
                                (first.prob_hispanic + last.prob_hispanic) / 2, 3
                            ),
                            "asian": round((first.prob_asian + last.prob_asian) / 2, 3),
                            "other": round((first.prob_other + last.prob_other) / 2, 3),
                        },
                    }
                )
            else:
                first = self.generate_first_name(ethnicity, gender, distribution)
                results.append(
                    {
                        "first_name": first.name,
                        "gender": first.gender,
                        "ethnicity_probabilities": {
                            "white": first.prob_white,
                            "black": first.prob_black,
                            "hispanic": first.prob_hispanic,
                            "asian": first.prob_asian,
                            "other": first.prob_other,
                        },
                    }
                )

        return results
