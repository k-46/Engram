"""Pydantic models for Engram engineering-history documents."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DocumentId = Annotated[
    str,
    Field(
        min_length=5,
        max_length=64,
        pattern=r"^[A-Z][A-Z0-9-]*-\d{3,}$",
        description="Stable, human-readable document identifier.",
    ),
]


class DocumentRelationship(BaseModel):
    """A directed relationship from one document to another."""

    model_config = ConfigDict(extra="forbid")

    relationship_type: Literal["related_to", "implements", "mitigates", "documents"]
    target_document_id: DocumentId


class DocumentMetadata(BaseModel):
    """Fields shared by every document type."""

    model_config = ConfigDict(extra="forbid")

    document_id: DocumentId
    title: str = Field(min_length=10, max_length=200)
    document_type: Literal["adr", "incident_report", "design_specification"]
    document_date: date
    status: str
    related_documents: list[DocumentId] = Field(default_factory=list)
    relationships: list[DocumentRelationship] = Field(default_factory=list)

    @field_validator("related_documents")
    @classmethod
    def unique_related_documents(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("related_documents must not contain duplicates")
        return value


class ArchitectureDecisionRecord(DocumentMetadata):
    """A decision, its alternatives, and its consequences."""

    document_type: Literal["adr"] = "adr"
    status: Literal["proposed", "accepted", "superseded", "retired"]
    context: str = Field(min_length=20)
    decision: str = Field(min_length=20)
    alternatives: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=20)
    consequences: list[str] = Field(min_length=1)
    supersedes: list[DocumentId] = Field(default_factory=list)

    @field_validator("supersedes")
    @classmethod
    def unique_superseded_documents(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("supersedes must not contain duplicates")
        return value


class IncidentReport(DocumentMetadata):
    """A production or operational incident and its follow-up work."""

    document_type: Literal["incident_report"] = "incident_report"
    status: Literal["investigating", "mitigated", "resolved", "closed"]
    severity: Literal["sev1", "sev2", "sev3", "sev4"]
    detected_at: date
    resolved_at: date | None = None
    impact: str = Field(min_length=20)
    root_cause: str = Field(min_length=20)
    resolution: str = Field(min_length=20)
    preventive_actions: list[str] = Field(min_length=1)

    @field_validator("resolved_at")
    @classmethod
    def resolution_not_before_detection(
        cls, value: date | None, info
    ) -> date | None:
        detected_at = info.data.get("detected_at")
        if value is not None and detected_at is not None and value < detected_at:
            raise ValueError("resolved_at cannot be before detected_at")
        return value


class DesignSpecification(DocumentMetadata):
    """A technical design and its implementation requirements."""

    document_type: Literal["design_specification"] = "design_specification"
    status: Literal["draft", "approved", "deprecated"]
    problem_statement: str = Field(min_length=20)
    architecture: str = Field(min_length=20)
    components: list[str] = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    apis: list[str] = Field(default_factory=list)
    technical_requirements: list[str] = Field(min_length=1)
    tradeoffs: list[str] = Field(default_factory=list)


Document = Annotated[
    ArchitectureDecisionRecord | IncidentReport | DesignSpecification,
    Field(discriminator="document_type"),
]


def validate_corpus(documents: list[Document]) -> list[Document]:
    """Validate IDs and relationship targets across a complete corpus."""

    document_by_id: dict[str, Document] = {}
    for document in documents:
        if document.document_id in document_by_id:
            raise ValueError(f"duplicate document_id: {document.document_id}")
        document_by_id[document.document_id] = document

    for document in documents:
        references = list(document.related_documents)
        references.extend(
            relationship.target_document_id
            for relationship in document.relationships
        )
        if isinstance(document, ArchitectureDecisionRecord):
            references.extend(document.supersedes)

        if document.document_id in references:
            raise ValueError(
                f"{document.document_id} cannot reference itself"
            )
        missing = sorted(set(references) - document_by_id.keys())
        if missing:
            raise ValueError(
                f"{document.document_id} references unknown documents: "
                + ", ".join(missing)
            )
        if isinstance(document, ArchitectureDecisionRecord):
            invalid_targets = [
                target
                for target in document.supersedes
                if not isinstance(document_by_id[target], ArchitectureDecisionRecord)
            ]
            if invalid_targets:
                raise ValueError(
                    f"{document.document_id}.supersedes must target ADRs: "
                    + ", ".join(invalid_targets)
                )
    return documents
