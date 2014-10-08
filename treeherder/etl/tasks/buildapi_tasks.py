"""
This module contains
"""
from celery import task, group
from treeherder.model.derived import RefDataManager
from treeherder.etl.buildapi import (RunningJobsProcess,
                                     PendingJobsProcess,
                                     Builds4hJobsProcess,
                                     Builds4hAnalyzer)
from treeherder.etl.pushlog import HgPushlogProcess


@task(name='fetch-buildapi-pending', time_limit=3*60)
def fetch_buildapi_pending():
    """
    Fetches the buildapi pending jobs api and load them to
    the objectstore ingestion endpoint
    """
    PendingJobsProcess().run()


@task(name='fetch-buildapi-running', time_limit=3*60)
def fetch_buildapi_running():
    """
    Fetches the buildapi running jobs api and load them to
    the objectstore ingestion endpoint
    """
    RunningJobsProcess().run()


@task(name='fetch-buildapi-build4h', time_limit=3*60)
def fetch_buildapi_build4h():
    """
    Fetches the buildapi running jobs api and load them to
    the objectstore ingestion endpoint
    """
    Builds4hJobsProcess().run()


@task(name='fetch-push-logs')
def fetch_push_logs():
    """
    Run several fetch_hg_push_log subtasks, one per repository
    """
    rdm = RefDataManager()
    try:
        repos = filter(lambda x: x['url'], rdm.get_all_repository_info())
        # create a group of subtasks and apply them
        g = group(fetch_hg_push_log.si(repo['name'], repo['url'])
                            for repo in repos if repo['dvcs_type'] == 'hg')
        g()
    finally:
        rdm.disconnect()


@task(name='fetch-hg-push-logs', time_limit=3*60)
def fetch_hg_push_log(repo_name, repo_url):
    """
    Run a HgPushlog etl process
    """
    process = HgPushlogProcess()
    process.run(repo_url + '/json-pushes/?full=1', repo_name)


@task(name='run-builds4h-analyzer')
def run_builds4h_analyzer():
    """
    Run a Builds4h Analysis process
    """
    process = Builds4hAnalyzer()
    process.run()


