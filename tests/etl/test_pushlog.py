import os
import json
import responses
from treeherder.etl.pushlog import HgPushlogProcess


def test_ingest_hg_pushlog(jm, initial_data, test_base_dir,
                           test_repository, mock_post_json_data, activate_responses):
    """ingesting a number of pushes should populate result set and revisions"""

    pushlog_path = os.path.join(test_base_dir, 'sample_data', 'hg_pushlog.json')
    pushlog_content = open(pushlog_path).read()
    pushlog_fake_url = "http://www.thisismypushlog.com"
    responses.add(responses.GET, pushlog_fake_url,
                  body=pushlog_content, status=200,
                  content_type='application/json')

    process = HgPushlogProcess()

    process.run(pushlog_fake_url, jm.project)

    pushes_stored = jm.get_jobs_dhub().execute(
        proc="jobs_test.selects.result_set_ids",
        return_type='tuple'
    )

    assert len(pushes_stored) == 10

    revisions_stored = jm.get_jobs_dhub().execute(
        proc="jobs_test.selects.revision_ids",
        return_type='tuple'
    )

    assert len(revisions_stored) == 15


def test_ingest_hg_pushlog_already_stored(jm, initial_data, test_base_dir,
                           test_repository, mock_post_json_data, activate_responses):
    """test that trying to ingest a push already stored doesn't doesn't affect
    all the pushes in the request,
    e.g. trying to store [A,B] with A already stored, B will be stored"""

    pushlog_path = os.path.join(test_base_dir, 'sample_data', 'hg_pushlog.json')
    pushlog_content = open(pushlog_path).read()
    pushes = json.loads(pushlog_content).values()
    first_push, second_push = pushes[0:2]

    pushlog_fake_url = "http://www.thisismypushlog.com/?full=1"

    # store the first push only
    first_push_json = json.dumps({"1": first_push})
    responses.add(responses.GET, pushlog_fake_url,
                  body=first_push_json, status=200,
                  content_type='application/json',
                  match_querystring=True,
                  )

    process = HgPushlogProcess()
    process.run(pushlog_fake_url, jm.project)

    pushes_stored = jm.get_jobs_dhub().execute(
        proc="jobs_test.selects.result_set_ids",
        return_type='tuple'
    )

    assert len(pushes_stored) == 1

    # store both first and second push
    first_and_second_push_json = json.dumps(
        {"1": first_push, "2": second_push}
    )
    second_push
    responses.add(
        responses.GET,
        pushlog_fake_url+"&fromchange=2c25d2bbbcd6ddbd45962606911fd429e366b8e1",
        body=first_and_second_push_json,
        status=200, content_type='application/json',
        match_querystring=True)

    process = HgPushlogProcess()

    process.run(pushlog_fake_url, jm.project)

    pushes_stored = jm.get_jobs_dhub().execute(
        proc="jobs_test.selects.result_set_ids",
        return_type='tuple'
    )

    assert len(pushes_stored) == 2
