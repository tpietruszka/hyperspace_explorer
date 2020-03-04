# Hyperspace explorer
Collection of tools meant to enable faster progress and reproducibility of results in ML/DL 
projects and competitions, without assuming too much about the projects themselves and used tools. 

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Introduction](#introduction)
  - [What is it useful for?](#what-is-it-useful-for)
  - [Goals](#goals)
  - [Glossary](#glossary)
- [Setup](#setup)
  - [Installation](#installation)
  - [Project structure](#project-structure)
- [Usage](#usage)
  - [Running a worker](#running-a-worker)
  - [Browsing experiment results](#browsing-experiment-results)
- [Possible access points, usage modes](#possible-access-points-usage-modes)
  - [CLI](#cli)
  - [Run queue + workers](#run-queue--workers)
  - [Interactive prototyping in Jupyter](#interactive-prototyping-in-jupyter)
  - [Running tests](#running-tests)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Introduction
### What is it useful for?
Meant to support a process where we have:
- a dataset, possibly pre-processed to some degree, that can be deterministically loaded (multiple versions of data? 
loading code should take an argument specifying which version to load)
- an objective - we only consider supervised ML problems here, and we need some quality metric (be it 
accuracy or AUROC of classification, RMSE of regression, or something else). The metric can be changed, multiple metrics also supported.

A common, useful approach is to then to quickly develop a simple version of the full pipeline:
1. loading the data
2. pre-processing, data augmentation, etc
3. the model logic (if not a ready-made solution - perhaps a custom neural architecture?)
4. model training procedure
5. scoring the model on the validation set 

Then the real work begins - multiple iterations of:
1. **developing and testing new versions of parts of the pipeline** - adding dimensions to the hyper-parameter 
space (e.g. different neural architecture, different kind of model altogether, different pre-trained network, different 
data pre-processing logic),
2. **optimizing hyper-parameters**,
3. inspecting how/when the model fails, and how it works - to guide further development,
4. (in some cases) periodically pushing new versions to production.
 
This package is meant to provide common utilities supporting workflows like those, regardless
of the frameworks/libraries in use or the structure of the problem to solve. It was born from 
common parts of multiple projects, often having a "weird" structure - e.g.:

- fitting multiple models with identical hyper-parameters to time-series from corresponding machines,
- periodic re-training of the model (also for time-series)
- testing the same approach on multiple subsets of the training set

The strength of the package lies in its modularity, minimal assumptions about what you need to do 
and how you need to do it. It is meant to get out of your way - your code should still work without it, 
ran the way you need - be it CLI, a notebook, etc.

### Goals
It should be possible to:
- store and analyze results of all past experiments,
- reproduce past results (-> store results together with hyper-parameters, data, versions of code, ...),
- easily re-run past experiments with some hyper-parameters changed,
- develop or inspect parts of the pipeline in a notebook, easily run all of it from there (TODO: instructions),
- extend the code's functionality and the hyper-parameter space; new hyper-params should always be added 
  with default values matching previous behaviour. Replacing pieces of logic with different ones, with different 
  hyper-parameters should be handled as well.
- queue runs from a notebook (e.g. generate a grid of HPs in some dimensions) and have them
  executed by worker processes (possibly distributed among multiple machines). Then close the notebook, or 
  add some more runs, never again waiting for computations to finish.
- install core parts of the project's package and use it in production code (if the code got ugly with too many
  options, write a new version of it, and compare results with the old version, all in the same environment)
- **use automatic hyper-parameter tuning algorithms**, informed by all past experiments during development. 

### Glossary
- `Run` - single execution of a `Task` with a specific config (set of parameters), concluded by calculation
of a quality metric (one or more). \
Example: training a classifier with the hyper-parameters provided in the config, calculating AUROC/accuracy/...
on the validation set. \
Each run gets its entry - including parameters, code versions, result metrics, additional meta-information -\
in the MongoDB database, `runs` collection.
- `Task` - fully specified problem to solve, and then compare different solutions to. \
Consists of a chosen 
`Scenario` and some parameters passed to it - e.g. which dataset to use, how big a sample of a training set
to use, etc. Each task should be specified as a .json file.
- `Scenario` - template of a `Task` without its parameters. When parameterized by `Task` parameters
and a `Run` config it can be executed, and should return a quality metric. Each `Scenario` is a class,
inheriting from `scenario_base.Scenario`. Its `.single_run()` method typically contains dataset construction, 
model construction, model training and evaluation.
    

## Setup
### Installation
Install with pip, as a normal python package.

Other than all the modules being made available for import, it will also make `hyperspace_worker.py` 
available in your system's PATH (or a specific virtual environment).

To use most of this package's functions a running instance of MongoDB will be needed.

### Project structure
TODO

## Usage
### Running a worker
Run a command `hyperspace_worker.py [path to tasks dir] [mongo db name]`.

**Important:** it has to be ran from a directory containing a `scenarios.py` module, which defines 
experiment scenarios allowed to be ran within the given project. The `hyperspace_worker.py` file 
should not be present in the folder.

Arguments:

- `path to tasks dir` - path to a directory containing `.json` files, describing each allowed `task` -
a parameterization of a `scenario`
- `mongo db name` - name of the mongoDB database to store results in
- optional params: mongoDB URI (if not localhost, or if password is required), interval to query for new tasks

### Browsing experiment results

This project (ab)uses [Sacred](https://github.com/IDSIA/sacred) to collect and store information about each run.

One of the benefits: we can use many ready-made dashboards for Sacred,
e.g.  [Omniboard](https://github.com/vivekratnavel/omniboard) - highly recommended, works out of the box, 
many impressive features. 


## Possible access points, usage modes
### CLI
TODO
### Run queue + workers
Start workers on 1 or more nodes, set them up to use the same database (which is also the task queue).
Workers are specific to one project - will only process tasks for the project they were started for.

Example code, usually ran from a notebook, to submit one task. From here, it is easy to e.g. submit a grid
of hyper-parameters for the workers to test.

```python
from hyperspace_explorer.queue import RunQueue
from pathlib import Path

tasks_dir = Path.cwd().resolve().parent / 'tasks'  # just an example - relative to the notebook
db_name = 'ulmfit_attention'
mongo_uri = 'localhost:27017'

q = RunQueue(mongo_uri, db_name, tasks_dir)
task_name = 'imdb_1k_sample_single'

conf = {
    'aggregation': {  # different additional parameters are available depending on `className`
        'className': 'BranchingAttentionAggregation',
        'agg_layers': [50, 10]
    },
    'classifier': { # this dict is passed to a specific function within a scenario, but polymorphism is not needed
        'lin_ftrs': [],
        'drop_mult': 0.5,
    },
    'training_schedule': { # even if we do not want to change any default parameters, className is required
        'className': 'DefaultSchedule',
    }
}
q.submit(task_name, conf)

```
The code above works with the project: https://github.com/tpietruszka/ulmfit_attention. 
In this case workers should be ran from within the inner `ulmfit_attention` directory.

### Interactive prototyping in Jupyter
TODO 
### Running tests
TODO
