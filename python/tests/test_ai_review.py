from copy import deepcopy

import pytest
from analyst_os_ai.review import approved_rows, checked_draft, review_template


def draft():
    return {
        "version": 1,
        "source": {
            "id": "00000000-0000-0000-0000-000000000001",
            "company_id": "00000000-0000-0000-0000-000000000002",
            "company_slug": "example",
            "source_url": "https://example.com/report.pdf",
            "sha256": "a" * 64,
            "page_count": 10,
            "fiscal_year": 2025,
        },
        "model_digest": "b" * 64,
        "pages": [{"page": 3, "text": "TEST ONLY company describes its operating segments."}],
        "bundle": {
            "company_slug": "example",
            "model_name": "test-only:1",
            "insights": [
                {
                    "section": "business_brief",
                    "title": "TEST ONLY business",
                    "text": "The source describes its operating segments.",
                    "confidence": "low",
                    "evidence": [
                        {
                            "source_url": "https://example.com/report.pdf",
                            "page": 3,
                            "quote": "company describes its operating segments.",
                        }
                    ],
                }
            ],
        },
    }


def test_pending_draft_cannot_publish():
    d = draft()
    with pytest.raises(ValueError, match="no explicitly approved"):
        approved_rows(d, review_template(d))


def test_exact_approval_and_stable_identity():
    d = draft()
    review = review_template(d)
    review["decisions"]["0"] = {
        "status": "approved",
        "reviewer": "TEST ONLY",
        "reviewed_at": "2020-01-01T00:00:00Z",
        "rationale": "Synthetic ephemeral test only",
    }
    assert approved_rows(d, review) == approved_rows(deepcopy(d), deepcopy(review))
    d["bundle"]["insights"][0]["text"] += " Changed."
    with pytest.raises(ValueError, match="exact draft"):
        approved_rows(d, review)


@pytest.mark.parametrize("change", ["quote", "page", "url", "company", "recommendation"])
def test_unsubstantiated_drafts_fail_closed(change):
    d = draft()
    item = d["bundle"]["insights"][0]
    if change == "quote":
        item["evidence"][0]["quote"] = "This quotation was never in the PDF."
    elif change == "page":
        item["evidence"][0]["page"] = 4
    elif change == "url":
        item["evidence"][0]["source_url"] = "https://wrong.example/report.pdf"
    elif change == "company":
        d["bundle"]["company_slug"] = "other"
    else:
        item["text"] = "Buy this company for guaranteed returns."
    with pytest.raises(ValueError):
        checked_draft(d)


def test_missing_reviewer_cannot_approve():
    d = draft()
    review = review_template(d)
    review["decisions"]["0"]["status"] = "approved"
    with pytest.raises(ValueError, match="reviewer and rationale"):
        approved_rows(d, review)
