import unittest

from source_capacity import (
    capacity_summary, interleave_sources_by_type, source_capacity_settings,
)


class SourceCapacityTests(unittest.TestCase):
    def test_maximum_safe_and_balanced_profiles_are_coherent(self):
        maximum = source_capacity_settings("maximum_safe", env={})
        balanced = source_capacity_settings("balanced", env={})
        self.assertEqual(maximum["ba_rotation_limit"], 220)
        self.assertEqual(maximum["ats_historical_board_cap"], 420)
        self.assertEqual(maximum["workday_extra_page_budget"], 16)
        self.assertEqual(maximum["linkedin_max_queries_per_run"], 40)
        self.assertEqual(maximum["linkedin_recovery_start_queries"], 1)
        self.assertEqual(maximum["linkedin_query_delay_seconds"], 30)
        self.assertEqual(balanced["ba_rotation_limit"], 44)
        self.assertEqual(balanced["ats_historical_board_cap"], 360)
        self.assertEqual(balanced["linkedin_max_queries_per_run"], 32)

    def test_focused_depth_uses_smaller_linkedin_and_workday_budgets(self):
        maximum = source_capacity_settings("maximum_safe", env={}, depth="focused")
        balanced = source_capacity_settings("balanced", env={}, depth="focused")
        self.assertEqual(maximum["linkedin_max_queries_per_run"], 8)
        self.assertEqual(maximum["workday_extra_page_budget"], 0)
        self.assertEqual(balanced["linkedin_max_queries_per_run"], 8)
        self.assertEqual(balanced["workday_extra_page_budget"], 0)

    def test_explicit_operator_caps_are_preserved(self):
        settings = source_capacity_settings("maximum_safe", env={
            "JOBSPY_RESULTS_PER_QUERY": "60",
            "JOBSPY_LINKEDIN_MAX_QUERIES_PER_RUN": "24",
            "JOBSPY_LINKEDIN_QUERY_DELAY_SECONDS": "20",
        })
        self.assertEqual(settings["jobspy_results_per_query"], 60)
        self.assertEqual(settings["linkedin_max_queries_per_run"], 24)
        self.assertEqual(settings["linkedin_query_delay_seconds"], 30)

    def test_invalid_profile_falls_back_to_maximum_safe(self):
        self.assertEqual(source_capacity_settings("unlimited", env={})["profile"],
                         "maximum_safe")

    def test_source_tasks_are_round_robin_fair_and_stable(self):
        tasks = [
            {"type": "bundesagentur", "slug": "ba-1"},
            {"type": "bundesagentur", "slug": "ba-2"},
            {"type": "workday", "slug": "wd-1"},
            {"type": "jobspy_indeed", "slug": "indeed"},
            {"type": "workday", "slug": "wd-2"},
            {"type": "arbeitnow", "slug": "arbeitnow"},
        ]
        ordered = interleave_sources_by_type(tasks)
        self.assertEqual(
            [(x["type"], x["slug"]) for x in ordered[:4]],
            [
                ("bundesagentur", "ba-1"),
                ("workday", "wd-1"),
                ("jobspy_indeed", "indeed"),
                ("arbeitnow", "arbeitnow"),
            ],
        )
        self.assertEqual([x["slug"] for x in ordered if x["type"] == "workday"],
                         ["wd-1", "wd-2"])

    def test_capacity_summary_reports_actual_planned_tasks_and_queue(self):
        settings = source_capacity_settings("maximum_safe", env={})
        tasks = [
            {"type": "bundesagentur", "slug": "ba"},
            {"type": "workday", "slug": "wd"},
            {"type": "jobspy_indeed", "slug": "indeed",
             "queries": ["quality", "cargo"]},
        ]
        summary = capacity_summary("maximum_safe", settings, tasks, {
            "total_query_terms": 900, "planned_queries": 16,
        })
        self.assertEqual(summary["planned"]["source_tasks"], 3)
        self.assertEqual(summary["planned"]["bundesagentur_tasks"], 1)
        self.assertEqual(summary["planned"]["ats_board_tasks"], 1)
        self.assertEqual(summary["planned"]["jobspy_platform_queries"], 2)
        self.assertEqual(summary["planned"]["linkedin_queue_terms"], 900)
        self.assertEqual(summary["planned"]["linkedin_batch_queries"], 16)


if __name__ == "__main__":
    unittest.main()
