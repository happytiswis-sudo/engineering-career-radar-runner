"""Offline tests for the resumable LinkedIn role queue; no provider calls."""
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from linkedin_role_queue import (
    build_linkedin_role_queue, complete_linkedin_batch,
    linkedin_capacity_settings, linkedin_queue_progress,
    prepare_linkedin_batch,
)

ROOT=Path(__file__).parents[1]
CATALOG=json.loads((ROOT/'role_catalog.json').read_text(encoding='utf8'))['roles']
NOW=datetime(2026,10,30,12,0,tzinfo=timezone.utc)


class LinkedInRoleQueueTests(unittest.TestCase):
    def test_all_catalog_titles_and_tracks_enter_fair_rotation_queue(self):
        queue=build_linkedin_role_queue(CATALOG)
        titles={r['title'].casefold() for r in CATALOG}
        tracks={r['track'] for r in CATALOG}
        self.assertEqual(len(titles),784)
        self.assertEqual(len(tracks),34)
        self.assertTrue(titles.issubset({x.casefold() for x in queue}))
        self.assertGreater(len(queue),len(titles))
        first_batch=prepare_linkedin_batch(CATALOG,env={},now=NOW)
        self.assertEqual(first_batch['plan']['catalog_role_count'],784)
        self.assertEqual(first_batch['plan']['catalog_track_count'],34)
        self.assertEqual(first_batch['plan']['batch_size'],40)
        self.assertEqual(len(first_batch['queries']),40)
        title_tracks={r['title'].casefold():r['track'] for r in CATALOG}
        first_batch_tracks={title_tracks[q.casefold()] for q in first_batch['queries']
                            if q.casefold() in title_tracks}
        self.assertEqual(len(first_batch_tracks),34,
                         'First LinkedIn batch must cover all 34 catalogue tracks before repeats');

    def test_explicit_roles_and_tracks_scope_the_queue_without_silent_truncation(self):
        roles=['Quality Engineer','Cargo Technician','Maintenance Planner']
        self.assertEqual(build_linkedin_role_queue(CATALOG,requested_roles=roles),roles)
        selected={'Airport Cargo, Freight & Logistics','Airport Operations, Apron & Turnaround'}
        queue=build_linkedin_role_queue(CATALOG,requested_tracks=sorted(selected))
        self.assertTrue(queue)
        title_tracks={r['title'].casefold():r['track'] for r in CATALOG}
        returned_titles={q.casefold() for q in queue if q.casefold() in title_tracks}
        self.assertTrue(all(title_tracks[q] in selected for q in returned_titles))
        scoped=prepare_linkedin_batch(CATALOG,requested_tracks=sorted(selected),env={},now=NOW)
        self.assertEqual(scoped['plan']['scope_track_count'],2)
        self.assertEqual(scoped['plan']['scope_role_count'],
                         sum(1 for r in CATALOG if r['track'] in selected))

    def test_successful_batch_advances_cursor_and_reports_capacity(self):
        plan=prepare_linkedin_batch(CATALOG,env={},now=NOW)
        state=complete_linkedin_batch(plan['state'],plan['plan'],{
            'attempted_queries':40,'completed_queries':40,'cursor_advance_count':40,
            'provider_rows':1200,'valid_postings':950
        },env={},now=NOW,run_id='123')
        self.assertEqual(state['cursor'],40)
        self.assertEqual(state['status'],'batch_complete')
        self.assertEqual(state['total_provider_rows'],1200)
        progress=linkedin_queue_progress(plan['plan'],state,{
            'attempted_queries':40,'completed_queries':40,'provider_rows':1200,
            'valid_postings':950
        })
        self.assertEqual(progress['attempted_queries'],40)
        self.assertEqual(progress['valid_postings'],950)
        self.assertGreater(progress['coverage_percent'],0)

    def test_429_does_not_consume_blocked_query_and_enforces_cooldown(self):
        plan=prepare_linkedin_batch(CATALOG,env={},now=NOW)
        blocked_at=NOW+timedelta(hours=48)
        state=complete_linkedin_batch(plan['state'],plan['plan'],{
            'attempted_queries':8,'completed_queries':7,'cursor_advance_count':7,
            'provider_rows':300,'valid_postings':220,
            'stop_reason':'HTTP 429 / rate limited'
        },env={},now=NOW,run_id='124')
        self.assertEqual(state['cursor'],7)
        self.assertEqual(state['status'],'rate_limited')
        self.assertEqual(state['rate_limit_count'],1)
        self.assertEqual(datetime.fromisoformat(state['blocked_until']),blocked_at)
        held=prepare_linkedin_batch(CATALOG,prior_state=state,env={},now=NOW+timedelta(hours=1))
        self.assertEqual(held['queries'],[])
        self.assertEqual(held['plan']['status'],'cooldown_active')
        reset_must_not_bypass=prepare_linkedin_batch(CATALOG,prior_state=state,
            env={'JOBSPY_LINKEDIN_RESET_PAUSE':'yes'},now=NOW+timedelta(hours=1))
        self.assertEqual(reset_must_not_bypass['queries'],[])
        self.assertEqual(reset_must_not_bypass['plan']['status'],'cooldown_active')
        resumed=prepare_linkedin_batch(CATALOG,prior_state=state,env={},now=NOW+timedelta(hours=49))
        self.assertEqual(resumed['plan']['start_cursor'],7)
        self.assertEqual(resumed['queries'][0],plan['queries'][7])

    def test_initial_cooldown_seed_prevents_first_run_retry_and_persists(self):
        env={'JOBSPY_LINKEDIN_INITIAL_COOLDOWN_UNTIL':'2026-10-31T14:34:48Z'}
        held=prepare_linkedin_batch(CATALOG,env=env,now=NOW)
        self.assertEqual(held['queries'],[])
        self.assertEqual(held['plan']['status'],'cooldown_active')
        self.assertEqual(held['state']['blocked_until'],'2026-10-31T14:34:48+00:00')
        self.assertEqual(held['state']['rate_limit_count'],1)

        resumed_at=datetime(2026,10,31,14,34,49,tzinfo=timezone.utc)
        resumed=prepare_linkedin_batch(
            CATALOG,prior_state=held['state'],env=env,now=resumed_at
        )
        self.assertTrue(resumed['queries'])
        self.assertEqual(resumed['plan']['status'],'ready')
        self.assertEqual(resumed['state']['blocked_until'],'')
        self.assertEqual(resumed['plan']['batch_size'],1)

    def test_recovery_ramp_starts_lower_then_grows_after_clean_batches(self):
        blocked=prepare_linkedin_batch(CATALOG,env={},now=NOW)
        state=complete_linkedin_batch(blocked['state'],blocked['plan'],{
            'attempted_queries':8,'completed_queries':7,'cursor_advance_count':7,
            'failed_queries':1,'stop_reason':'HTTP 429 / rate limited'
        },env={},now=NOW)
        resumed_at=NOW+timedelta(hours=49)
        first=prepare_linkedin_batch(CATALOG,prior_state=state,env={},now=resumed_at)
        self.assertEqual(first['plan']['batch_size'],1)
        self.assertEqual(first['plan']['configured_max_queries_per_run'],40)

        state=complete_linkedin_batch(first['state'],first['plan'],{
            'attempted_queries':1,'completed_queries':1,'cursor_advance_count':1,
            'failed_queries':0
        },env={},now=resumed_at,run_id='clean-1')
        second=prepare_linkedin_batch(CATALOG,prior_state=state,env={},now=resumed_at)
        self.assertEqual(second['plan']['batch_size'],2)

        state=complete_linkedin_batch(second['state'],second['plan'],{
            'attempted_queries':2,'completed_queries':2,'cursor_advance_count':2,
            'failed_queries':0
        },env={},now=resumed_at,run_id='clean-2')
        third=prepare_linkedin_batch(CATALOG,prior_state=state,env={},now=resumed_at)
        self.assertEqual(third['plan']['batch_size'],4)

        state=complete_linkedin_batch(third['state'],third['plan'],{
            'attempted_queries':4,'completed_queries':4,'cursor_advance_count':4,
            'failed_queries':0
        },env={},now=resumed_at,run_id='clean-3')
        full=prepare_linkedin_batch(CATALOG,prior_state=state,env={},now=resumed_at)
        self.assertEqual(full['plan']['batch_size'],8)

    def test_cooldown_progress_retains_total_queue_terms(self):
        env={'JOBSPY_LINKEDIN_INITIAL_COOLDOWN_UNTIL':'2026-10-31T14:34:48Z'}
        held=prepare_linkedin_batch(CATALOG,env=env,now=NOW)
        progress=linkedin_queue_progress(held['plan'],held['state'],{})
        self.assertGreater(progress['total_query_terms'],784)
        self.assertEqual(progress['planned_queries'],0)
        self.assertEqual(progress['status'],'cooldown_active')

    def test_initial_cooldown_seed_never_shortens_a_later_provider_block(self):
        plan=prepare_linkedin_batch(CATALOG,env={},now=NOW)
        later=NOW+timedelta(days=2)
        state={**plan['state'],'blocked_until':later.isoformat()}
        held=prepare_linkedin_batch(
            CATALOG,prior_state=state,
            env={'JOBSPY_LINKEDIN_INITIAL_COOLDOWN_UNTIL':'2026-10-31T14:34:48Z'},
            now=NOW
        )
        self.assertEqual(held['queries'],[])
        self.assertEqual(datetime.fromisoformat(held['state']['blocked_until']),later)

    def test_403_pauses_until_explicit_operator_reset(self):
        plan=prepare_linkedin_batch(CATALOG,env={},now=NOW)
        state=complete_linkedin_batch(plan['state'],plan['plan'],{
            'attempted_queries':1,'failed_queries':1,'cursor_advance_count':0,
            'stop_reason':'HTTP 403 / source blocked'
        },env={},now=NOW)
        self.assertTrue(state['paused'])
        held=prepare_linkedin_batch(CATALOG,prior_state=state,env={},now=NOW+timedelta(days=2))
        self.assertEqual(held['queries'],[])
        self.assertEqual(held['plan']['status'],'paused_access_denied')
        reset=prepare_linkedin_batch(CATALOG,prior_state=state,
            env={'JOBSPY_LINKEDIN_RESET_PAUSE':'yes'},now=NOW+timedelta(days=2))
        self.assertTrue(reset['queries'])
        self.assertFalse(reset['state']['paused'])

    def test_capacity_and_pacing_settings_are_bounded(self):
        self.assertEqual(linkedin_capacity_settings({},'deep')['max_queries_per_run'],40)
        self.assertEqual(linkedin_capacity_settings({},'focused')['max_queries_per_run'],8)
        cfg=linkedin_capacity_settings({
            'JOBSPY_LINKEDIN_MAX_QUERIES_PER_RUN':'999',
            'JOBSPY_LINKEDIN_QUERY_DELAY_SECONDS':'90',
            'JOBSPY_LINKEDIN_RATE_LIMIT_COOLDOWN_HOURS':'0'
        })
        self.assertEqual(cfg['max_queries_per_run'],40)
        self.assertEqual(cfg['query_delay_seconds'],30)
        self.assertEqual(cfg['rate_limit_cooldown_hours'],1)
        self.assertEqual(linkedin_capacity_settings({},'deep')['query_delay_seconds'],30)
        self.assertEqual(linkedin_capacity_settings({},'deep')['recovery_start_queries'],1)
        self.assertEqual(linkedin_capacity_settings({},'deep')['rate_limit_cooldown_hours'],48)


if __name__=='__main__':
    unittest.main()
