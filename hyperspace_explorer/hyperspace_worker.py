#!/usr/bin/env python
from pathlib import Path
import traceback
import time
import argparse
import sys
import copy
import json
from sacred import observers, Experiment, settings
from hyperspace_explorer.queue import RunQueue, QueuedRun
from hyperspace_explorer.configurables import fill_in_defaults

# because of the way things get imported, the default discovery strategies do not work
settings.SETTINGS.DISCOVER_SOURCES = "sys"
settings.SETTINGS.DISCOVER_DEPENDENCIES = "sys"


def process_queue(tasks_dir: Path, db_name: str, mongo_uri: str, sleep_time: int):
    observer = observers.MongoObserver(mongo_uri, db_name=db_name)
    q = RunQueue(mongo_uri, db_name, tasks_dir)
    while True:
        t = q.fetch_one()
        if t is None:
            print("No available tasks in the queue. Sleeping.")
            time.sleep(sleep_time)
            continue
        try:
            single_run(t, observer)
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
        finally:
            q.remove(t)


def single_run(to_run: QueuedRun, observer: observers.RunObserver):
    params = fill_in_defaults(to_run.params)
    base_dir = Path(scenarios.__file__).parent
    ex = Experiment(to_run.task_name, base_dir=base_dir)
    ex.observers.append(observer)
    ex.add_config(params)
    task_rnd_seed = json.load(to_run.task_description_file.open()).get("seed", None)
    if task_rnd_seed is not None:
        # needs to be set before run to make sense with sacred
        ex.add_config({"seed": task_rnd_seed})

    @ex.main
    def ex_main(_config, _run):
        #  task desc should always stay effectively the same, but logging as resource just in case
        task = json.load(ex.open_resource(to_run.task_description_file, "r"))
        scenario = scenarios.Scenario.from_config(task["Scenario"])
        scenario.setup_sacred(_run)
        res = scenario.single_run(_config)
        return res[0]

    run_res = ex.run()
    return run_res


def main():
    desc = (
        "Run experiments from a MongoDB-based queue. \nShould be ran from a folder containing "
        "a `scenarios` module, defining the possible scenarios to run. Concrete tasks - "
        "sets of parameters for scenarios - should be defined in json files, in the `tasks_dir` folder"
    )
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "tasks_dir",
        help="Path to a folder storing task json files, absolute or relative",
        type=lambda s: Path(s).resolve(),
    )
    parser.add_argument("db_name", help="MongoDB database name")
    parser.add_argument(
        "--mongo-uri",
        help="URI of the MongoDB server instance",
        default="localhost:27017",
    )
    parser.add_argument("--sleep-time", type=int, default=30)
    args = parser.parse_args()
    process_queue(args.tasks_dir, args.db_name, args.mongo_uri, args.sleep_time)


if __name__ == "__main__":
    orig_path = copy.copy(sys.path)
    sys.path.insert(0, str(Path.cwd()))
    try:
        import scenarios
    except ImportError as e:
        print(
            "Failed import of `scenarios.py`. This script should be ran from a directory containing it."
        )
        print(e)
        exit(1)
    sys.path = orig_path
    main()
