from name_generator.llm_validator import get_validator

validator = get_validator()

# Validate name combination
result = validator.validate_name_combination(
    first_name="Maria", last_name="Garcia", ethnicity="hispanic"
)
print(result["is_valid"])

# Generate middle name
middle = validator.generate_middle_name(
    first_name="Maria", last_name="Garcia", ethnicity="hispanic", gender="F"
)
print(middle)
