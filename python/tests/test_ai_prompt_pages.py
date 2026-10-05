import unittest

from analyst_os_ai.chunking import DocumentChunk
from analyst_os_ai.pipeline import AIOutputValidationError, validate_insight_bundle
from analyst_os_ai.prompts import build_analysis_prompt


class CitationPageTests(unittest.TestCase):
    def test_example_uses_supplied_physical_page(self):
        prompt = build_analysis_prompt(
            company_slug="reliance-industries",
            source_url="https://example.com/report.pdf",
            chunks=[DocumentChunk(4, "Evidence"), DocumentChunk(2, "Other evidence")],
        )
        self.assertIn("Allowed physical PDF pages: [2, 4].", prompt)
        self.assertIn('"page": 2, "section": null', prompt)
        self.assertNotIn('"page": 1, "section": null', prompt)

    def test_empty_evidence_has_no_invented_example(self):
        with self.assertRaises(ValueError):
            build_analysis_prompt(
                company_slug="reliance-industries",
                source_url="https://example.com/report.pdf",
                chunks=[],
            )

    def test_unsupplied_citation_still_rejected(self):
        payload = {
            "company_slug": "reliance-industries",
            "model_name": "test:1",
            "insights": [{
                "section": "business_brief",
                "title": "Business",
                "text": "A test interpretation.",
                "confidence": "low",
                "evidence": [{
                    "source_url": "https://example.com/report.pdf",
                    "page": 1,
                    "quote": "This is a test source quotation.",
                }],
            }],
        }
        with self.assertRaisesRegex(AIOutputValidationError, "not supplied"):
            validate_insight_bundle(
                payload,
                expected_company_slug="reliance-industries",
                expected_model_name="test:1",
                allowed_source_url="https://example.com/report.pdf",
                allowed_pages={2, 3, 4},
            )


if __name__ == "__main__":
    unittest.main()
