"""Domain exception hierarchy for the Emotion Recognition System (ERS)."""


class ERSError(Exception):
    """Base exception for all ERS runtime and domain errors."""


class ERSConfigurationError(ERSError):
    """Raised when engine configuration parameters are invalid or contradictory."""


class ERSValidationError(ERSError):
    """Raised when input data violates contract constraints, dimensions, or formats."""


class ERSModelUnavailableError(ERSError):
    """Raised when a requested model adapter or weights file is uninstalled or unavailable."""


class ERSModelExecutionError(ERSError):
    """Raised when model inference execution fails unexpectedly."""


class ERSModelIntegrityError(ERSError):
    """Raised when model artifact checksum, tensor contract, or manifest verification fails."""


class ERSQualityRejectionError(ERSError):
    """Raised when input signal quality falls below the minimum usable threshold."""


class ERSAlignmentError(ERSError):
    """Raised when sensory observations cannot be aligned within the multimodal temporal window."""


class ERSPrivacyConsentError(ERSError):
    """Raised when processing is attempted without valid user consent or after consent revocation."""


class ERSResourceExhaustedError(ERSError):
    """Raised when internal memory, buffer limits, or compute budgets are exceeded."""


class ERSLifecycleError(ERSError):
    """Raised when an illegal lifecycle transition is invoked."""
