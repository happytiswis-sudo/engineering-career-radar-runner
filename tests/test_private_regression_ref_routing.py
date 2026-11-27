from pathlib import Path
import unittest


class PrivateRegressionRefRoutingTests(unittest.TestCase):
    def test_docs_prs_use_private_main_before_generic_runner_sha_fallback(self):
        workflow = Path(".github/workflows/private-scanner-regression.yml").read_text(encoding="utf-8")
        docs_route = 'elif [[ "$EVENT_NAME" == "pull_request" && "$PR_TITLE" == docs:* ]]; then\n            # Documentation/handover PR SHAs belong to this public runner repo, not the private scanner repo.\n            # Validate the current private main baseline instead of checking out an unrelated SHA.\n            candidate="main"'
        generic_route = 'elif [[ "$EVENT_NAME" == "pull_request" && -z "${PRIVATE_REF:-}" ]]; then\n            candidate="$PR_HEAD_SHA"'
        self.assertIn(docs_route, workflow)
        self.assertIn(generic_route, workflow)
        self.assertLess(workflow.index(docs_route), workflow.index(generic_route))


if __name__ == "__main__":
    unittest.main()
