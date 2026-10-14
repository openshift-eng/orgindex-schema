"""Canonical, versioned pydantic schema for the organizational comprehensive index.

Import the top-level model and the schema version:

    from orgindex_schema import ComprehensiveIndexModel, SCHEMA_VERSION
"""

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
    "conformance_problems",
    "generate_json_schema",
]
