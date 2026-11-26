"""Domain-specific exceptions for agricultural product substitution and merchant ranking."""


class SubstitutionError(Exception):
    """Base exception for all product substitution and ranking errors."""
    pass


class ActiveIngredientMismatchError(SubstitutionError):
    """Raised when candidate product active ingredient does not match the reference active ingredient."""
    pass


class IncompatibleConcentrationUnitError(SubstitutionError):
    """Raised when reference and substitute concentration units cannot be reconciled."""
    pass


class IncompatibleFormulationError(SubstitutionError):
    """Raised when product formulation cannot be applied via the prescribed application method."""
    pass


class UnregisteredProductError(SubstitutionError):
    """Raised when a candidate product lacks statutory legal registration."""
    pass


class CropDiseaseMismatchError(SubstitutionError):
    """Raised when a candidate product is not registered for the target crop or disease."""
    pass


class InvalidDosageError(SubstitutionError):
    """Raised when base dosage, concentration, or search radius is non-positive or invalid."""
    pass
