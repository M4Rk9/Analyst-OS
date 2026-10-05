"""Regression tests for exact, page-bound source passage selection."""
import unittest
from unittest.mock import patch

from analyst_os_ai.chunking import DocumentChunk
from analyst_os_ai.passages import build_passages, resolve_selection
from analyst_os_ai.pipeline import generate_insights, AIOutputValidationError
from analyst_os_ai.prompts import build_selection_prompt
from pydantic import ValidationError


class PassageTests(unittest.TestCase):
    def setUp(self):
        self.text = 'Management states:\nIndia’s growth remains a priority.\nThis is an aspiration.'
        self.chunks = [DocumentChunk(page=4, text=self.text)]
        self.passages = build_passages(self.chunks)
        self.payload = {'company_slug': 'example', 'insights': [{
            'section': 'management_outlook', 'title': 'Management priority',
            'text': 'Management describes growth as a priority.', 'confidence': 'low',
            'evidence': [{'quote_id': 'Q0001'}]}]}

    def resolve(self):
        return resolve_selection(self.payload, passages=self.passages,
                                 source_url='https://example.com/report.pdf', model='local')

    def test_preserves_exact_text_and_physical_page(self):
        evidence = self.resolve()['insights'][0]['evidence'][0]
        self.assertEqual(evidence['quote'], self.text)
        self.assertEqual(evidence['page'], 4)

    def test_all_slices_are_exact_substrings(self):
        text = ('A long source line with curly apostrophe ’ and newline.\n' * 70) + 'tiny'
        passages = build_passages([DocumentChunk(page=9, text=text)])
        self.assertGreater(len(passages), 1)
        for passage in passages:
            self.assertIn(passage.quote, text)
            self.assertTrue(20 <= len(passage.quote) <= 800)
            self.assertEqual(passage.page, 9)

    def test_unknown_id_rejected(self):
        self.payload['insights'][0]['evidence'][0]['quote_id'] = 'Q9999'
        with self.assertRaises(ValueError):
            self.resolve()

    def test_model_cannot_override_trusted_citation(self):
        for key, value in [('page', 2), ('quote', 'invented quote'),
                           ('source_url', 'https://evil.example')]:
            with self.subTest(key=key):
                evidence = self.payload['insights'][0]['evidence'][0]
                evidence[key] = value
                with self.assertRaises(ValidationError):
                    self.resolve()
                del evidence[key]

    def test_empty_or_short_context_rejected(self):
        for text in ['', 'tiny']:
            with self.assertRaises(ValueError):
                build_passages([DocumentChunk(page=4, text=text)])

    def test_prompt_requests_only_ids(self):
        prompt = build_selection_prompt(company_slug='example', passages=self.passages)
        self.assertIn('"quote_id": "Q0001"', prompt)
        self.assertIn('Never output quotes, URLs, page numbers, or model_name', prompt)

    def test_generation_attaches_trusted_citations(self):
        with patch('analyst_os_ai.pipeline.generate_json', return_value=self.payload):
            bundle = generate_insights(company_slug='example',
                source_url='https://example.com/report.pdf', chunks=self.chunks, model='local')
        self.assertEqual(bundle.insights[0].evidence[0].quote, self.text)
        self.assertEqual(bundle.insights[0].evidence[0].page, 4)
        self.assertEqual(bundle.model_name, 'local')

    def test_generation_rejects_wrong_company(self):
        self.payload['company_slug'] = 'different'
        with patch('analyst_os_ai.pipeline.generate_json', return_value=self.payload):
            with self.assertRaises(AIOutputValidationError):
                generate_insights(company_slug='example', source_url='https://example.com/report.pdf',
                                  chunks=self.chunks, model='local')


if __name__ == '__main__':
    unittest.main()
