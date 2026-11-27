from pathlib import Path
import unittest


class PrivateRegressionRefRoutingTests(unittest.TestCase):
    def test_validate_private_branch_marker_uses_matching_private_branch_name(self):
        workflow = Path(".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        self.assertIn("PR_HEAD_REF: ${{ github.event.pull_request.head.ref }}", workflow)
        marker = 'PR_TITLE:-}" == *"[validate-private-branch]"*'
        self.assertIn(marker, workflow)
        start = workflow.index(marker)
        end = workflow.index('elif [[ "$EVENT_NAME" == "pull_request" && "$PR_TITLE" == docs:* ]]; then', start)
        self.assertIn('candidate="$PR_HEAD_REF"', workflow[start:end])

    def test_docs_prs_use_private_main_before_generic_runner_sha_fallback(self):
        workflow = Path(".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        docs_marker = 'PR_TITLE" == docs:*'
        fallback_marker = 'candidate="$PR_HEAD_SHA"'
        self.assertIn(docs_marker, workflow)
        docs_start = workflow.index(docs_marker)
        docs_end = workflow.index(fallback_marker, docs_start)
        docs_route = workflow[docs_start:docs_end]
        self.assertIn('candidate="main"', docs_route)
        self.assertLess(docs_start, workflow.index('PR_HEAD_SHA', docs_end))


if __name__ == "__main__":
    unittest.main()
