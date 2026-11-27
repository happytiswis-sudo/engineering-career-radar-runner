from pathlib import Path
import unittest


class PrivateRegressionRefRoutingTests(unittest.TestCase):
    def test_docs_prs_use_private_main_before_generic_runner_sha_fallback(self):
        workflow = Path(".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        docs_marker = 'PR_TITLE" == docs:*'
        generic_marker = 'PR_TITLE:-}" == *"[cloro-ai-diagnostics-postmerge]"*'
        fallback_marker = 'candidate="$PR_HEAD_SHA"'
        self.assertIn(docs_marker, workflow)
        docs_start = workflow.index(docs_marker)
        docs_end = workflow.index(fallback_marker, docs_start)
        docs_route = workflow[docs_start:docs_end]
        self.assertIn('candidate="main"', docs_route)
        self.assertLess(docs_start, workflow.index('PR_HEAD_SHA', docs_end))
        self.assertIn(generic_marker, workflow)


if __name__ == "__main__":
    unittest.main()
