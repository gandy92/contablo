# ConTabLo
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Description
**ConTabLo** is a python package providing a **Con**figurable **Tab**le **Lo**ader.

With ConTabLo, it is possible to define import configurations for a number of different CSV file formats with the goal to import them into a defined table format, with defined data types for each column. Given a number of configurations, each CSV file can be matched to its configuration via meta data like delimiter, file format and column headers.

A CLI tool is provided that can automatically generate configuration files templates from a number of CSV files. These templates can be edited to get a working configuration. Additionally, a json-schema can created from a configuration file to support editing the configurations.

## Installation
ConTabLo can be installed from the [Python Package Index](https://pypi.org/):
```shell
python3 -m pip install contablo
```

# Usage
Used as a command line tool, ConTabLo provides the following functionality:
```shell
$ contablo -h
Usage: contablo [OPTIONS] COMMAND [ARGS]...

  CLI tool to the ConTabLo python package.

Options:
  -v, --verbose
  -h, --help     Show this message and exit.

Commands:
  convert         Load the given CSV file(s) based on their...
  mk-import-tmpl  Create an input configuration template for the given...
  mk-schema       Create a JSON schema for validation of JSON based...
```

## Example

### Create an import template from a number of CSV files
Any application that uses ConTabLo would probably have a good idea on the composition of the table, data should be imported into.
This idea can be expressed by creating a list of FieldSpec objects (or rather objects of classes that follow the FieldSpec protocol). Since the commandlinetool ```contablo``` is rather generic, it provides a way to initialize this table specification from a simple JSON file like the following:
```JSON
[
    { "name": "date", "type": "date", "help": "Date of payment" },
    { "name": "payee","type": "string", "help": "Person or institution sending or receiving the payment" },
    { "name": "note", "type": "string", "help": "Transaction notes" },
    { "name": "iban", "type": "string", "help": "Payee IBAN" },
    { "name": "bic", "type": "string", "help": "Payee BIC, if applicable" },
    { "name": "amount", "type": "number", "help": "Payment amount" },
    { "name": "balance", "type": "number", "help": "New account balance" }
]
```

With this, we can create an import template from a number of CSV files that already contains hints for possible target fields:
```shell
$ contablo mk-import-tmpl -t fieldspec-banking.json banking*.csv -o bank-tmpl
Found 1 distict file formats:
  # 1: 2 files, iso-8859-1 encoded, with 1 chunks.
       # 1: 5 columns, 87 samples
            Datum;Name;Text;Betrag (EUR);Saldo (EUR)
            30.10.2024;"Some random payee Inc.";"SEPA-Basislasts [..] 24 Kunden-Referenz: xxxyyyzzz";"-217,50";"539,11"
  Template was written to bank-tmpl-20241103_165348-01.json
```

The resulting template now contains specifications for each of the five columns, e.g.:

```JSON
{
  "columns": [
    {
      "label": "Datum",
      "field": "date",
      "format": "dd.mm.yyyy"
    },
    {
      "label": "Name",
      "field": "payee|note|iban|bic",
      "format": "",
      "samples": [
        "Some random payee Inc.",
        "Another random payee Inc.",
        "Someone completely different"
      ]
    },
    {
      "label": "Text",
      "field": "payee|note|iban|bic",
      "format": "",
      "samples": [
        "Note 1",
        "Note 2"
      ]
    },
    {
      "label": "Betrag (EUR)",
      "field": "amount|balance",
      "format": "-1.000,00"
    },
    {
      "label": "Saldo (EUR)",
      "field": "amount|balance",
      "format": "1.000,00"
    }
  ]
}
```
Each "field" entry contains suggestions for target fields to choose from, depending on the type of input (again, see subclasses of FieldSpec for builtin types).

The same template after a manual cleaup results in an import specification:
```JSON
{
  "columns": [
    {
      "label": "Datum",
      "field": "date",
      "format": "dd.mm.yyyy"
    },
    {
      "label": "Name",
      "field": "payee"
    },
    {
      "label": "Text",
      "field": "note"
    },
    {
      "label": "Betrag (EUR)",
      "field": "amount",
      "format": "-1.000,00"
    },
    {
      "label": "Saldo (EUR)",
      "field": "balance",
      "format": "1.000,00"
    }
  ]
}
```
Note, how the sample and empty format elements were removed and the field entries were reduced to the desired target field name. The labels must stay unchanged, they are an essential identification marker matching a CSV import file to the appropriate import configuration. Since it is no longer a template, we rename it to a more appropriate name, e.g. ```bank-import-config.json```.

We are now ready to convert the type of CSV files described by the import specification:
```shell
$ contablo convert -t fieldspec-banking.json -c bank-import-config.json banking-*.csv -o merged_data.csv
```

# Contributing
If you want to contribute to this project, please use the following steps:

1. Fork the project.
2. Create a new branch (git checkout -b feature/awesome-feature).
3. Commit your changes (git commit -m 'Add some feature').
4. Push to the branch (git push origin feature/awesome-feature).
5. Open a pull request.

# Commit Message Structure

This projects aims to follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary) guidelines.

When writing commit messages, use one of the following categories to clearly describe the purpose of your commit:

- **feat** / **feature**: ✨  Introducing new features
- **fix** / **bugfix**: 🐛  Addressing bug fixes
- **perf**: 🚀  Enhancing performance
- **refactor**: 🔄  Refactoring code - **Not displayed in CHANGELOG**
- **test** / **tests**: ✅  Adding or updating tests - **Not displayed in CHANGELOG**
- **build** / **ci**: 🛠️  Build system or CI/CD updates - **Not displayed in CHANGELOG**
- **doc** / **docs**: 📚  Documentation changes - **Not displayed in CHANGELOG**
- **style**: 🎨  Code style or formatting changes - **Not displayed in CHANGELOG**
- **chore**: 🔧  Miscellaneous chores
- **other**: 🌟  Other significant changes

## Example Commit Messages

- `feat: Add cool new feature`
- `fix: Resolve unexpected behavior with translation`

# License
This project is licensed under the MIT License.
