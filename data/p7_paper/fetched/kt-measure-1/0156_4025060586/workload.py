import os, hashlib, json
os.environ["PREFECT_HOME"] = "/tmp/kt_20972/home"
os.makedirs("/tmp/kt_20972/home", exist_ok=True)
os.environ["PREFECT_LOGGING_SETTINGS_PATH"] = "/tmp/kt_20972/home/logging.yml"
os.environ["PREFECT_PROFILES_PATH"] = "/tmp/kt_20972/home/profiles.toml"
os.environ["PREFECT_LOGGING_TO_API_ENABLED"] = "false"
os.environ["PREFECT_LOGGING_LEVEL"] = "WARNING"
os.environ["PREFECT_LOGGING_TO_API_WHEN_MISSING_FLOW"] = "ignore"
from prefect.server.api.server import SubprocessASGIServer
from prefect.task_runners import ProcessPoolTaskRunner
from prefect.settings import temporary_settings, PREFECT_API_URL
from prefect import task


@task
def add(a, b):
    return a * 3 + b


def main():
    srv = SubprocessASGIServer()
    srv.start()
    os.environ["PREFECT_API_URL"] = srv.api_url
    results = []
    try:
        with temporary_settings({PREFECT_API_URL: srv.api_url}):
            # two runner lifecycles: second start exercises cache invalidation
            for rnd in range(2):
                with ProcessPoolTaskRunner(max_workers=4) as r:
                    fs = [r.submit(add, {"a": i, "b": rnd}) for i in range(20)]
                    results.append([f.result() for f in fs])
                    r.cancel_all()
    finally:
        srv.stop()
    print(results[0][:5], results[1][:5])
    print(hashlib.sha256(json.dumps(results).encode()).hexdigest())


if __name__ == "__main__":
    main()
