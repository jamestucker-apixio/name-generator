"""
Data loader for Harvard Dataverse voter file dataset.

Downloads and processes the name-ethnicity dataset from:
https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/SGKW0K
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

import requests

# Dataset URLs from Harvard Dataverse
DATAVERSE_BASE_URL = "https://dataverse.harvard.edu/api/access/datafile"

# File IDs from the Dataverse dataset
FIRST_NAMES_FILE_ID = "7060179"  # first_nameRaceProbs.tab
SURNAMES_FILE_ID = "7060183"  # last_nameRaceProbs.tab

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DATA_DIR / "names.db"


class DataLoader:
    """Handles downloading and processing name-ethnicity datasets."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "names.db"

    def download_file(self, file_id: str, output_filename: str) -> Path:
        """
        Download a file from Harvard Dataverse.

        Args:
            file_id: The Dataverse file ID
            output_filename: Name to save the file as

        Returns:
            Path to the downloaded file
        """
        url = f"{DATAVERSE_BASE_URL}/{file_id}"
        output_path = self.data_dir / output_filename

        if output_path.exists():
            print(f"File {output_filename} already exists, skipping download")
            return output_path

        print(f"Downloading {output_filename}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded {output_filename}")
        return output_path

    def parse_tab_file(
        self, file_path: Path, is_first_name: bool = False
    ) -> List[Dict]:
        """
        Parse a tab-separated file from the dataset.

        Args:
            file_path: Path to the tab file
            is_first_name: Whether this is a first names file (vs surnames)

        Returns:
            List of dictionaries with normalized name data
        """
        import csv

        results = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")

            for row in reader:
                # Strip quotes from name and convert to title case
                name = row["name"].strip('"').strip().title()

                if not name:
                    continue

                # Map column names from dataset format to our database format
                normalized = {
                    "name": name,
                    "gender": None,  # Gender not provided in this dataset
                    "count": 100,  # Default count (not provided in dataset)
                    "prob_white": float(row.get("whi", 0)),
                    "prob_black": float(row.get("bla", 0)),
                    "prob_hispanic": float(row.get("his", 0)),
                    "prob_asian": float(row.get("asi", 0)),
                    "prob_other": float(row.get("oth", 0)),
                }

                results.append(normalized)

        return results

    def create_database(self):
        """Create SQLite database with name tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create first names table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS first_names (
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
        """)

        # Create surnames table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surnames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                count INTEGER,
                prob_white REAL,
                prob_black REAL,
                prob_hispanic REAL,
                prob_asian REAL,
                prob_other REAL
            )
        """)

        # Create indices for faster lookups
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_first_names_name ON first_names(name)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_surnames_name ON surnames(name)")

        conn.commit()
        conn.close()
        print("Database created successfully")

    def import_data(self, first_names_data: List[Dict], surnames_data: List[Dict]):
        """
        Import name data into SQLite database.

        Args:
            first_names_data: List of first name dictionaries
            surnames_data: List of surname dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Import first names
        print("Importing first names...")
        for row in first_names_data:
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO first_names
                    (name, gender, count, prob_white, prob_black, prob_hispanic, prob_asian, prob_other)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row.get("name", ""),
                        row.get("gender", ""),
                        int(row.get("count", 0)),
                        float(row.get("prob_white", 0)),
                        float(row.get("prob_black", 0)),
                        float(row.get("prob_hispanic", 0)),
                        float(row.get("prob_asian", 0)),
                        float(row.get("prob_other", 0)),
                    ),
                )
            except (ValueError, KeyError) as e:
                print(f"Error importing first name {row}: {e}")

        # Import surnames
        print("Importing surnames...")
        for row in surnames_data:
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO surnames
                    (name, count, prob_white, prob_black, prob_hispanic, prob_asian, prob_other)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row.get("name", ""),
                        int(row.get("count", 0)),
                        float(row.get("prob_white", 0)),
                        float(row.get("prob_black", 0)),
                        float(row.get("prob_hispanic", 0)),
                        float(row.get("prob_asian", 0)),
                        float(row.get("prob_other", 0)),
                    ),
                )
            except (ValueError, KeyError) as e:
                print(f"Error importing surname {row}: {e}")

        conn.commit()
        conn.close()
        print("Data import complete")

    def setup_database(self, skip_download: bool = False):
        """
        Download datasets and set up the database.

        Args:
            skip_download: If True, use existing files instead of downloading
        """
        # Download or locate files
        if skip_download:
            first_names_file = self.data_dir / "first_names.tab"
            surnames_file = self.data_dir / "surnames.tab"

            if not first_names_file.exists() or not surnames_file.exists():
                raise FileNotFoundError(
                    "Data files not found. Run without skip_download=True to download."
                )
        else:
            first_names_file = self.download_file(
                FIRST_NAMES_FILE_ID, "first_names.tab"
            )
            surnames_file = self.download_file(SURNAMES_FILE_ID, "surnames.tab")

        # Parse tab-separated files
        print("Parsing first names file...")
        first_names_data = self.parse_tab_file(first_names_file, is_first_name=True)
        print(f"Loaded {len(first_names_data):,} first names")

        print("Parsing surnames file...")
        surnames_data = self.parse_tab_file(surnames_file, is_first_name=False)
        print(f"Loaded {len(surnames_data):,} surnames")

        # Create and populate database
        self.create_database()
        self.import_data(first_names_data, surnames_data)

        print(f"\nDatabase setup complete at {self.db_path}")
        return self.db_path


def main():
    """CLI entry point for data loader."""
    loader = DataLoader()
    loader.setup_database()


if __name__ == "__main__":
    main()
