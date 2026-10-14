"""Canonical pydantic models for the on-disk organizational comprehensive index.

``ComprehensiveIndexModel`` is the top-level ``{metadata, lookups, indexes}``
shape the org-indexer writes and every consumer reads.
"""

from pydantic import BaseModel, ConfigDict, Field

from .version import SCHEMA_VERSION

# Immutable, tolerant reads: unknown fields are ignored rather than rejected.
_CONFIG = ConfigDict(frozen=True, extra="ignore")


class ParentRef(BaseModel):
    model_config = _CONFIG

    name: str = ""
    type: str = ""  # team | org | pillar | team_group | cohort | component


class GroupTypeInfo(BaseModel):
    model_config = _CONFIG

    name: str = ""  # team | org | pillar | team_group | cohort | component | system | ...
    visualize: bool = False
    visualize_group: list[str] | None = None


class SlackChannelInfo(BaseModel):
    model_config = _CONFIG

    channel: str = ""
    channel_id: str = ""
    description: str = ""
    types: list[str] = Field(default_factory=list)


class SlackAliasInfo(BaseModel):
    model_config = _CONFIG

    alias: str = ""
    description: str = ""


class SlackConfigInfo(BaseModel):
    model_config = _CONFIG

    channels: list[SlackChannelInfo] = Field(default_factory=list)
    aliases: list[SlackAliasInfo] = Field(default_factory=list)


class RoleInfo(BaseModel):
    model_config = _CONFIG

    people: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    description: str = ""


class JiraInfo(BaseModel):
    """``component`` is set on component entries and empty on hierarchy entities."""

    model_config = _CONFIG

    project: str = ""
    component: str = ""
    description: str = ""
    view: str = ""
    types: list[str] = Field(default_factory=list)


class RepoInfo(BaseModel):
    """On-disk key is ``repo_name``, not ``repo``."""

    model_config = _CONFIG

    repo_name: str = ""
    description: str = ""
    branch: str = ""
    path: str = ""
    roles: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)


class EmailInfo(BaseModel):
    model_config = _CONFIG

    address: str = ""
    name: str = ""
    description: str = ""


class ResourceInfo(BaseModel):
    model_config = _CONFIG

    name: str = ""
    url: str = ""
    description: str = ""


class EscalationContactInfo(BaseModel):
    """In the PII-free index ``name``/``description`` are ``"[REDACTED]"`` and ``url`` is blank."""

    model_config = _CONFIG

    name: str = ""
    url: str = ""
    description: str = ""


class ContextItemInfo(BaseModel):
    """``source_entity``/``source_type`` are set on ``resolved_context`` and empty on raw ``context``."""

    model_config = _CONFIG

    types: list[str] = Field(default_factory=list)
    name: str = ""
    description: str | None = None
    url: str | None = None
    owner: str | None = None
    inheritance: str = "additive"  # additive | supersedes
    source_entity: str = ""
    source_type: str = ""


class RelatedComponentInfo(BaseModel):
    model_config = _CONFIG

    component_path: str = ""
    types: list[str] = Field(default_factory=list)


class GroupInfo(BaseModel):
    model_config = _CONFIG

    type: GroupTypeInfo | None = None
    resolved_people_uid_list: list[str] = Field(default_factory=list)
    resolved_roles: list[RoleInfo] = Field(default_factory=list)
    slack: SlackConfigInfo | None = None
    jiras: list[JiraInfo] = Field(default_factory=list)
    repos: list[RepoInfo] = Field(default_factory=list)
    keywords: list[str] | None = None
    emails: list[EmailInfo] = Field(default_factory=list)
    resources: list[ResourceInfo] = Field(default_factory=list)
    escalation: list[EscalationContactInfo] = Field(default_factory=list)
    component_roles: list[str] = Field(default_factory=list)
    context: list[ContextItemInfo] = Field(default_factory=list)
    resolved_context: list[ContextItemInfo] = Field(default_factory=list)


class EmployeeEntry(BaseModel):
    model_config = _CONFIG

    uid: str = ""
    full_name: str = ""
    email: str | None = None
    job_title: str | None = None
    github_id: str | None = None
    possible_github_ids: list[str] = Field(default_factory=list)
    manager_uid: str | None = None
    slack_uid: str | None = None
    timezone: str | None = None


class HierarchyEntity(BaseModel):
    """Shared by teams/orgs/pillars/team_groups/cohorts. The entity type lives in
    ``group.type.name`` and the collection key, not a top-level ``uid``/``type``."""

    model_config = _CONFIG

    name: str = ""
    description: str = ""
    parent: ParentRef | None = None
    parent_id: str = ""  # present only with an identity map
    stable_id: str = ""  # present only with an identity map
    group: GroupInfo | None = None


class ComponentInner(BaseModel):
    """Here ``parent`` is a file-path string, unlike the top-level :class:`ParentRef`."""

    model_config = _CONFIG

    type: GroupTypeInfo | None = None
    repos: list[RepoInfo] = Field(default_factory=list)
    jiras: list[JiraInfo] = Field(default_factory=list)
    resources: list[ResourceInfo] = Field(default_factory=list)
    related_components: list[RelatedComponentInfo] = Field(default_factory=list)
    parent: str = ""
    context: list[ContextItemInfo] = Field(default_factory=list)
    resolved_context: list[ContextItemInfo] = Field(default_factory=list)


class ComponentEntry(BaseModel):
    """Components are not identity-mapped, so they carry no ``stable_id``/``parent_id``."""

    model_config = _CONFIG

    name: str = ""
    description: str | None = None
    parent: ParentRef | None = None
    repos_list: list[str] = Field(default_factory=list)
    component: ComponentInner | None = None


class Lookups(BaseModel):
    model_config = _CONFIG

    employees: dict[str, EmployeeEntry] = Field(default_factory=dict)
    teams: dict[str, HierarchyEntity] = Field(default_factory=dict)
    orgs: dict[str, HierarchyEntity] = Field(default_factory=dict)
    pillars: dict[str, HierarchyEntity] = Field(default_factory=dict)
    team_groups: dict[str, HierarchyEntity] = Field(default_factory=dict)
    cohorts: dict[str, HierarchyEntity] = Field(default_factory=dict)
    components: dict[str, ComponentEntry] = Field(default_factory=dict)


class MembershipEntry(BaseModel):
    model_config = _CONFIG

    name: str = ""
    type: str = ""
    stable_id: str = ""  # present only with an identity map


class MembershipIndexInfo(BaseModel):
    model_config = _CONFIG

    membership_index: dict[str, list[MembershipEntry]] = Field(default_factory=dict)


class SlackIdMappings(BaseModel):
    model_config = _CONFIG

    slack_uid_to_uid: dict[str, str] = Field(default_factory=dict)


class GitHubIdMappings(BaseModel):
    model_config = _CONFIG

    github_id_to_uid: dict[str, str] = Field(default_factory=dict)


class JiraOwner(BaseModel):
    model_config = _CONFIG

    name: str = ""
    type: str = ""


class ComponentOwner(BaseModel):
    model_config = _CONFIG

    name: str = ""
    type: str = ""
    ownership_types: list[str] = Field(default_factory=list)


class Indexes(BaseModel):
    """``jira`` maps ``project -> component -> [owner]`` with the literal key
    ``"_project_level"`` for project-level ownership; ``component_ownership`` maps
    ``component_name -> [owner]``."""

    model_config = _CONFIG

    membership: MembershipIndexInfo = Field(default_factory=MembershipIndexInfo)
    slack_id_mappings: SlackIdMappings = Field(default_factory=SlackIdMappings)
    github_id_mappings: GitHubIdMappings = Field(default_factory=GitHubIdMappings)
    jira: dict[str, dict[str, list[JiraOwner]]] = Field(default_factory=dict)
    component_ownership: dict[str, list[ComponentOwner]] = Field(default_factory=dict)


class Metadata(BaseModel):
    model_config = _CONFIG

    schema_version: str = SCHEMA_VERSION
    builders: list[str] = Field(default_factory=list)
    context_type_descriptions: dict[str, str] = Field(default_factory=dict)
    data_version: str = ""
    generated_at: str = ""
    pii_free: bool = False
    supported_queries: list[str] = Field(default_factory=list)
    total_employees: int = 0
    total_orgs: int = 0


class ComprehensiveIndexModel(BaseModel):
    model_config = _CONFIG

    metadata: Metadata = Field(default_factory=Metadata)
    lookups: Lookups = Field(default_factory=Lookups)
    indexes: Indexes = Field(default_factory=Indexes)
