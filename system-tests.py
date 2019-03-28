import logging
import sys

from oci import config
from oci import gerrit
from oci import jenkins
from oci import output

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s")

logging = logging.getLogger("system-tests")

change = sys.argv[1]

if len(sys.argv) > 2:
    engine_version = sys.argv[2]
else:
    engine_version = "master"

suite_type = "basic"

cfg = config.load()

ga = gerrit.API(host=cfg.gerrit.host)

ja = jenkins.API(
    host=cfg.jenkins.host,
    user_id=cfg.jenkins.user_id,
    api_token=cfg.jenkins.api_token)

output.info("[ 1/8 ] Getting build info for change %s", change)
info = ga.build_info(change)

output.info("[ 2/8 ] Starting build-artifacts job for %s", info)
queue_url = ja.run(
    url=info["url"], ref=info["ref"], stage="build-artifacts")

output.info("[ 3/8 ] Waiting for queue item %s", queue_url)
job_url = ja.wait_for_queue(queue_url)

output.info("[ 4/8 ] Waiting for job %s", job_url)
result = ja.wait_for_job(job_url)

if result != "SUCCESS":
    output.fail("Build artifacts %s failed", job_url)
    sys.exit(1)

output.info("[ 5/8 ] Starting oVirt system tests %s suite with custom "
         "repos %s",
         suite_type, job_url)
queue_url = ja.build(
    "ovirt-system-tests_manual",
    parameters={
        "CUSTOM_REPOS": job_url,
        "ENGINE_VERSION": engine_version,
        "SUITE_TYPE": suite_type,
    }
)

output.info("[ 6/8 ] Waiting for queue item %s", queue_url)
job_url = ja.wait_for_queue(queue_url)

output.info("[ 7/8 ] Waiting for job %s", job_url)
result = ja.wait_for_job(job_url)

if result != "SUCCESS":
    output.failure("System tests failed with: %s", result)
    sys.exit(1)

output.success("System tests completed successfully, congratulations!")