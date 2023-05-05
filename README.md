# Beyond Typosquatting, An in-depth Look at Package Confusability

This is the artifact for the package confusability paper. This project implements the detection rules for the categories defined by our paper. The detection rules are implemented in `core`


## What is included
The dataset collected and the evaluation tools for the dataset.
The core detection implementations
Tools used to implement various parts

## Running the detection tools
Displays typo-squatting categories exhibited by adversarial package WRT base package:

```
$ python typomind <base_package_name> <potentially_malicious_package_name>
```

Learn more about flags and usage:
```
$ python typomind -h
```
