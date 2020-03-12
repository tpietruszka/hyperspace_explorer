import copy
from typing import *
import pymongo
from .utils import (
    flatten,
    unique_suffixes,
    drop_constant_columns,
    lists_to_tuples,
    requires_analysis_extra,
    pd,
)

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

    def fetch_results(
        self,
        query: Optional[Dict] = None,
        projection_extra: Optional[Dict] = None,
        order: Optional[List[Tuple]] = None,
        limit: int = 0,
    ) -> List[Dict]:
        """
        Fetches results of completed runs.

        :param query: MongoDB-style dict of conditions, e.g. {'key.nestedKey': 'val'}
        :param projection_extra: MongoDB-style dict of {'feat_name': 1} or similar
        :param order: each tuple is e.g. ('feat_name', pymongo.ASCENDING)
        :param limit: how many to fetch, 0 - fetch all
        :return: list of dicts, each dict representing a run
        """
        if query is None:
            query = {}
        projection = copy.copy(PROJECTION_RESULTS)
        if projection_extra:
            projection.update(projection_extra)
        if order is None:
            order = ORDER_RESULT_DESCENDING

        runs = self.find_runs(
            query, completed_only=True, sort=order, projection=projection, limit=limit
        )
        return runs

    @staticmethod
    @requires_analysis_extra
    def results_comparison(
        results: List[Dict], hide_const_cols: bool = True
    ) -> "pd.DataFrame":
        """
        Prepares a DataFrame comparing results of runs, given output of `fetch_results()`

        Requires Pandas.

        :param results: results, as returned by `fetch_results()`
        :param hide_const_cols: hide all columns with only 1 unique value?
        :return: a DataFrame indexed with run ids, comparing config params and results
        """
        df = pd.DataFrame([flatten(r) for r in results])
        df = df.set_index("_id")
        df.index.name = "id"
        df = df.rename(columns=unique_suffixes(df.columns))
        df = lists_to_tuples(df)
        if hide_const_cols:
            df = drop_constant_columns(df)
        return df

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
