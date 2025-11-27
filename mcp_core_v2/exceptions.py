"""Custom exceptions for MCP Core v2."""

class MCPError(Exception):
    """Base exception for all MCP errors."""
    pass


class InvalidSpecError(MCPError):
    """Raised when project specification is invalid or incomplete."""
    pass


class UnsupportedProjectError(MCPError):
    """Raised when project type is not supported by MCP."""
    pass


class CatalogLookupError(MCPError):
    """Raised when catalog item cannot be found."""
    pass


class SimulationError(MCPError):
    """Raised when electrical simulation fails."""
    pass


class ComplianceError(MCPError):
    """Raised when design violates electrical standards."""
    pass


class ValidationError(MCPError):
    """Raised when input validation fails."""
    pass
