"""Canonical, versioned pydantic schema for the organizational comprehensive index.

Import the top-level model and the schema version:

    from orgindex_schema import ComprehensiveIndexModel, SCHEMA_VERSION

``__version__`` is the installed *package* version (derived from the git tag at
build time); ``SCHEMA_VERSION`` is the on-disk *contract* version. Their majors
move together but they are distinct numbers — see COMPATIBILITY.md.
"""

# Aliased: a plain ``version`` would be clobbered by the ``.version`` submodule,
# which import binds as an attribute on this package.
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from .models import (
    ComponentEntry,
    ComponentInner,
    ComponentOwner,
    ComprehensiveIndexModel,
    ContextItemInfo,
    EmailInfo,
    EmployeeEntry,
    EscalationContactInfo,
    GitHubIdMappings,
    GroupInfo,
    GroupTypeInfo,
    HierarchyEntity,
    Indexes,
    JiraInfo,
    JiraOwner,
    Lookups,
    MembershipEntry,
    MembershipIndexInfo,
    Metadata,
    ParentRef,
    RelatedComponentInfo,
    RepoInfo,
    ResourceInfo,
    RoleInfo,
    SlackAliasInfo,
    SlackChannelInfo,
    SlackConfigInfo,
    SlackIdMappings,
)
from .schema import generate_json_schema
from .validation import conformance_problems
from .version import SCHEMA_VERSION

try:
    __version__ = _pkg_version("orgindex-schema")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "0.0.0+unknown"

__all__ = [
    "SCHEMA_VERSION",
    "ComponentEntry",
    "ComponentInner",
    "ComponentOwner",
    "ComprehensiveIndexModel",
    "ContextItemInfo",
    "EmailInfo",
    "EmployeeEntry",
    "EscalationContactInfo",
    "GitHubIdMappings",
    "GroupInfo",
    "GroupTypeInfo",
    "HierarchyEntity",
    "Indexes",
    "JiraInfo",
    "JiraOwner",
    "Lookups",
    "MembershipEntry",
    "MembershipIndexInfo",
    "Metadata",
    "ParentRef",
    "RelatedComponentInfo",
    "RepoInfo",
    "ResourceInfo",
    "RoleInfo",
    "SlackAliasInfo",
    "SlackChannelInfo",
    "SlackConfigInfo",
    "SlackIdMappings",
    "__version__",
    "conformance_problems",
    "generate_json_schema",
]
