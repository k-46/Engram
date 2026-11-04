import unittest
from datetime import date
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from engram.corpus import load_corpus
from engram.models import (
    ArchitectureDecisionRecord,
    Document,
    IncidentReport,
    validate_corpus,
)


DOCUMENT_ADAPTER = TypeAdapter(Document)
CORPUS_PATH = Path(__file__).parents[1] / "data" / "sample_corpus.json"


class DocumentValidationTests(unittest.TestCase):
    def test_sample_corpus_is_valid_and_interconnected(self):
        documents = load_corpus(CORPUS_PATH)

        self.assertEqual(len(documents), 12)
        self.assertEqual(
            sum(
                isinstance(document, ArchitectureDecisionRecord)
                for document in documents
            ),
            5,
        )
        self.assertEqual(
            sum(isinstance(document, IncidentReport) for document in documents),
            3,
        )
        self.assertTrue(
            any(
                document.supersedes
                for document in documents
                if isinstance(document, ArchitectureDecisionRecord)
            )
        )

    def test_document_type_and_status_are_discriminated(self):
        with self.assertRaises(ValidationError):
            DOCUMENT_ADAPTER.validate_python(
                {
                    "document_id": "ADR-999",
                    "title": "An invalid status example",
                    "document_type": "adr",
                    "document_date": "2024-01-01",
                    "status": "closed",
                    "context": "This context is long enough to pass basic validation.",
                    "decision": "This decision is also long enough to pass validation.",
                    "alternatives": ["Keep the old approach"],
                    "rationale": "This rationale is long enough to pass basic validation.",
                    "consequences": ["The team must document the change"],
                }
            )

    def test_incident_rejects_resolution_before_detection(self):
        with self.assertRaisesRegex(ValidationError, "resolved_at"):
            IncidentReport(
                document_id="IR-999",
                title="An incident with impossible dates",
                document_date=date(2024, 1, 2),
                status="resolved",
                severity="sev3",
                detected_at=date(2024, 1, 2),
                resolved_at=date(2024, 1, 1),
                impact="A sufficiently detailed impact description for the test.",
                root_cause="A sufficiently detailed root cause description for the test.",
                resolution="A sufficiently detailed resolution description for the test.",
                preventive_actions=["Add a regression test"],
            )

    def test_corpus_rejects_unknown_relationship_target(self):
        document = ArchitectureDecisionRecord(
            document_id="ADR-999",
            title="A decision with an unknown relationship",
            document_date=date(2024, 1, 1),
            status="accepted",
            context="This context is long enough to pass basic validation.",
            decision="This decision is also long enough to pass validation.",
            alternatives=["Keep the old approach"],
            rationale="This rationale is long enough to pass basic validation.",
            consequences=["The team must document the change"],
            related_documents=["DS-999"],
        )

        with self.assertRaisesRegex(ValueError, "unknown documents"):
            validate_corpus([document])


if __name__ == "__main__":
    unittest.main()
