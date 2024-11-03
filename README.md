# CoTaLo
**CoTaLo** is a python package providing a **Co**nfigurable **Ta**ble **Lo**ader.

With CoTaLo, it is possible to define import configurations for a number of different CSV file formats with the goal to import them into a defined table format, with defined data types for each column. Given a number of configurations, each CSV file can be matched to its configuration via meta data like delimiter, file format and column headers.

A CLI tool is provided that can automatically generate configuration files templates from a number of CSV files. These templates can be edited to get a working configuration. Additionally, a json-schema can created from a configuration file to support editing the configurations.

# CoTaLo
BlackClue is licensed unter the [MIT License](LICENSE).

# Installation
BlackClue can be installed from the [Python Package Index](https://pypi.org/):
```bash
python3 -m pip install cotalo
```

# Usage
Used as a command line tool, CoTaLo provides the following functionality:
```bash
$ cotalo -h
```

Leave bug reports and feature requests on https://github.com/gandy92/cotalo.

# History
## 0.1.0
First release on GitHub
