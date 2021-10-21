# Changelog

Note: This changelog is not exhaustive. Each release also include small bug fixes and cleanups.

## 0.11 (2021-10-21)

* Brightway 2.5 compatibility
* Removed `DatabaseExplorer`
* Removed `ParameterFinder`
* Deprecated `SerializedLCAReport`

## 0.10 (2021-05-06)

* Add `compare_activities_by_grouped_leaves` function.
* Add `find_differences_in_inputs` function.
* Add `compare_activities_by_lcia_score` function.
* Add `print_recursive_calculation` and `print_recursive_supply_chain` utility functions.
* Add dependencies on `pandas` and [tabulate](https://pypi.org/project/tabulate/).

### 0.9.5 (2019-11-06)

* Merge [PR #2](https://bitbucket.org/cmutel/brightway2-analyzer/pull-requests/2/multiple-methods-secondary-tags-and/commits), allowing for more powerful tagged graph traversal
* Fix error in nonunitary production for ``traverse_tagged_databases``.

### 0.9.4 (2017-04-17)

* Fix license text

### 0.9.3 (2017-04-11)

* Cleaned up setup and license

### 0.9.1 (2016-07-14)

* Compatibility with bw2data 2.3

## 0.9 (2016-04-09)

* Py3 compatibility
* Updates for compatibility with downstream changes

## 0.8 (2015-03-07)

* Compatibility with bw2calc 1.0 (split products and activities)
* Add ordered matrix graph

## 0.7 (2014-12-09)

Thanks Bernhard Steubing for good ideas and bugfixes.

* ENHANCEMENT: Add amount to annotated top processes and emissions.
* BUGFIX: Propagate **kwargs** in contribution analysis.

### 0.6.1 (2014-08-30)

* ENHANCMENT: Add ouroboros health check (processes which consume their own outcome)

## 0.6 (2014-08-29)

* FEATURE: Database health check! Does a number of tests on a Database to see if potential problems can be identified.

### 0.5.2 (2014-07-30)

Updated dependencies.

### 0.5.1 (2014-04-16)

* CHANGE: ContributionAnalysis.annotated_top_* will automatically reverse LCA object dictionaries if needed.

## 0.5 (2014-01-29)

* CHANGE: Compatibility fixes with bw2data 0.12 and bw2calc 0.11
