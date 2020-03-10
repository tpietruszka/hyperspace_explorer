from typing import *
import pymongo

RUNS_COLLECTION = "runs"
MONGO_URI_DEFAULT = "mongodb://localhost:27017"
STATUS_COMPLETED = "COMPLETED"


PROJECTION_RESULTS = {"config": 1, "result": 1}
ORDER_RESULT_DESCENDING = [("result", pymongo.DESCENDING)]


class Study:
    def __init__(self, db_name: str, mongo_uri: str = MONGO_URI_DEFAULT):
        self.db_name = db_name
        self.mongo_uri = mongo_uri
        self._client = pymongo.MongoClient(mongo_uri)
        self.c = self._client[db_name][RUNS_COLLECTION]

    def get_task_names(self) -> List[str]:
        return self.c.distinct("experiment.name")

    def get_task(self, name: str) -> "Task":
        return Task(name, self.db_name, self.mongo_uri)


class Task:
    def __init__(self, name: str, db_name: str, mongo_uri: str = MONGO_URI_DEFAULT):
        self.name = name
        self.db_name = db_name
        self.mongo_uri = mongo_uri
        self._client = pymongo.MongoClient(mongo_uri)
        self.c = self._client[db_name][RUNS_COLLECTION]

    def get_run(self, run_id: int) -> Dict:
        run = self.c.find_one(run_id)
        assert (
            run["experiment"]["name"] == self.name
        ), f"Given run id: {run_id} belongs to a different task: {run['experiment']['name']}!"
        return run

    def get_params(self, run_id: int) -> Dict:
        run = self.get_run(run_id)
        params = run["config"]
        if "seed" in params.keys():
            del params["seed"]
        return params

    def fetch_results(self, query: Optional[Dict] = None) -> List[Dict]:
        # TODO: add order setting
        # TODO: add an option to add custom columns (from metrics, info, others?)
        if query is None:
            query = {}
        runs = self.find_runs(
            query,
            completed_only=True,
            sort=ORDER_RESULT_DESCENDING,
            projection=PROJECTION_RESULTS,
        )
        return runs

    def compare_best(self):
        pass  # TODO: implement

    def find_runs(
        self, query: Dict, completed_only: bool = True, **kwargs
    ) -> List[Dict]:
        """Like MongoDBClient.find, but only retrieves entries related to this task"""
        conditions = [{"experiment.name": self.name}, query]
        if completed_only:
            conditions.append({"status": STATUS_COMPLETED})
        query_full = {"$and": conditions}
        runs = list(self.c.find(query_full, **kwargs))
        return runs

    def get_all_ids(self) -> List[int]:
        runs = self.find_runs({}, projection={"_id": 1})
        return [r["_id"] for r in runs]

    def get_completed_ids(self) -> List[int]:
        runs = self.find_runs({"status": STATUS_COMPLETED}, projection={"_id": 1})
        return [r["_id"] for r in runs]
