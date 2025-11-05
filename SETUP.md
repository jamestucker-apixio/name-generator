# Setup Guide

This guide will help you set up the name generator with the Harvard Dataverse dataset.

## Option 1: Automatic Setup (Recommended - Once File IDs Are Updated)

The easiest way to set up the database is to use the built-in setup command:

```bash
name-generator --setup
```

However, this requires updating the file IDs in `src/name_generator/data_loader.py` to match the actual Harvard Dataverse file IDs.

## Option 2: Manual Setup

If the automatic setup doesn't work, you can manually download and set up the data:

### Step 1: Download the Dataset

1. Visit the Harvard Dataverse dataset page:
   https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/SGKW0K

2. Look for files containing:
   - First names with ethnicity probabilities
   - Surnames with ethnicity probabilities

3. Download the relevant CSV or tab-delimited files

### Step 2: Inspect the Data Format

The dataset files should contain columns similar to:
- `name` or `firstname`/`surname`
- `gender` (for first names)
- `count` or `frequency`
- `prob_white`, `prob_black`, `prob_hispanic`, `prob_asian`, `prob_other` (or similar ethnicity probability columns)

### Step 3: Update the Data Loader

Edit `src/name_generator/data_loader.py` to match the actual:
- File IDs or URLs from Dataverse
- Column names in the CSV files
- File format (CSV, TSV, etc.)

### Step 4: Create the Database

Once you've updated the data loader, run:

```bash
python -m name_generator.data_loader
```

Or use the CLI command:

```bash
name-generator --setup
```

## Option 3: Alternative Data Sources

If you can't access the Harvard Dataverse dataset, you can use alternative sources:

### US Census Bureau Surname List

The Census Bureau provides a surname list with ethnicity probabilities:

```bash
# Download from Census API
curl "https://api.census.gov/data/2010/surname?get=NAME,COUNT,PROP_WHITE,PROP_BLACK,PROP_HISPANIC,PROP_ASIAN,PROP_2PRACE,PROP_AIAN&RANK=1:1000" > data/census_surnames.json
```

### Creating a Custom Dataset

You can create your own dataset following this schema:

**First Names Table:**
```sql
CREATE TABLE first_names (
    name TEXT NOT NULL,
    gender TEXT,  -- 'M' or 'F'
    count INTEGER,
    prob_white REAL,
    prob_black REAL,
    prob_hispanic REAL,
    prob_asian REAL,
    prob_other REAL
);
```

**Surnames Table:**
```sql
CREATE TABLE surnames (
    name TEXT NOT NULL,
    count INTEGER,
    prob_white REAL,
    prob_black REAL,
    prob_hispanic REAL,
    prob_asian REAL,
    prob_other REAL
);
```

Save as `data/names.db` and the generator will use it automatically.

## Testing the Setup

Once you've set up the database, test it:

```bash
# Generate a few names
name-generator --count 5

# Test specific ethnicities
name-generator --count 5 --ethnicity hispanic
name-generator --count 5 --ethnicity asian
name-generator --count 5 --ethnicity black

# Test different output formats
name-generator --count 10 --format json
```

## Troubleshooting

### Error: "Database not found"

- Make sure you've run `name-generator --setup` or manually created the database
- Check that the database file exists at `data/names.db`
- Try specifying a custom database path with `--db-path`

### Error: "No names found for ethnicity"

- Your database may not have enough names for that ethnicity
- Try lowering the `--min-probability` threshold:
  ```bash
  name-generator --ethnicity asian --min-probability 0.20
  ```

### Data Download Issues

If you have trouble downloading from Harvard Dataverse:

1. Check the dataset page for alternative download methods
2. Contact the dataset authors for access
3. Use alternative data sources (Census Bureau, other academic datasets)
4. Create a smaller custom dataset for testing

## Next Steps

Once setup is complete:

1. Read the [README.md](README.md) for usage instructions
2. Try the Python library API
3. Explore different ethnic distributions
4. Run the test suite: `pytest tests/`

## Additional Resources

- **Harvard Dataverse Dataset**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/SGKW0K
- **Research Paper**: https://www.nature.com/articles/s41597-023-02202-2
- **Census Bureau Surnames**: https://www.census.gov/data/developers/data-sets/surnames.html
- **CFPB Proxy Methodology**: https://github.com/cfpb/proxy-methodology
