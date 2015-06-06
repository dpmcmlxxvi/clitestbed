clitestbed
================================================================================

The Command Line Test Bed (clitestbed) runs a set of tests on a command line
application and generates a summary report of the test pass/fail performance.
The Test Bed runs a collection of Test Sets where each Test Set contains
multiple Test Cases. Both the Test Sets and Test Cases are defined by JSON
configuration files.

###Test Set configuration file

The main test set configuration file is a JSON formatted file. It can have
multiple sections, one for each Test Set. Sections can have custom
names which defines the Test Set. A Test Set executes a set of test
cases defined by their own JSON file. Each Test Set section has the
following properties:

| Property        | Description  | Required |
| --------------: |:-------------| :------: |
| **EXECUTABLE**  | Executable path | Yes |
| **OUTDIR**      | Output directory to write test bed results. | Yes |
| **TESTCASES**   | List of paths to test case files. Alternatively, use TESTDIR instead if all are in the same directory. | No |
| **TESTDIR**     | Path to directory containing files to test. If both, TESTCASES and TESTDIR are defined then their lists are combined. | No |
| **LOGFILE**     | Log file to write out test set results (optional) | No |
| **LOGLEVEL**    | Logging level: CRITICAL, ERROR, WARNING, INFO, DEBUG (optional) | No |
| **PATH**        | Multi-line list of paths to add to the system PATH environment variable | No |
| **SUCCESSCODE** | Executable success return code (default = 0) | No |
 
For example,

    {
        "Sample test set with a test directory": {
            "EXECUTABLE": "app.exe",
            "SUCCESSCODE": "1",
            "TESTDIR": "C:/testdir/",
            "OUTDIR": "C:/output/",
            "PATH": "C:/externals/",
            "LOGFILE": "testset.log",
            "LOGLEVEL": "DEBUG"
        },
        "Sample test set with a list of cases": {
           "EXECUTABLE": "app.exe",
           "TESTCASES": ["C:/testdir/case1.ini", "C:/testdir/case3.ini"],
           "OUTDIR": "C:/output/",
           "LOGFILE": "testset.log",
           "LOGLEVEL": "CRITICAL"
        }
    }

###Test Case argument file

The Test Case format has two sections **TEST** and **ARGUMENTS**. The
**TEST** section has three properties:

| Property        | Description  | Required |
| --------------: |:-------------| :------: |
| **DESCRIPTION** | Text description of the test case | Yes |
| **OUTSUBDIR**   | Sub-directory to export results (relative to test set OUTPUTDIR) | Yes |
| **LOGFILE**     | Path to a log file to which the executable output will be redirected. | Yes |

The **ARGUMENTS** section can contain any sequence of key=value pairs that
will be space separated, concatenated, and appended to the executable path and
executed by the OS. The value can be left empty for a flag that does not
require value or for a positional argument

    {
        "TEST": {
            "DESCRIPTION": "This is test #1.",
            "OUTSUBDIR": "mycase",
            "LOGFILE": "test1.log"
        },
        "ARGUMENTS": {
            "-f": "",
            "-i": "in.txt",
            "-o": "out.txt",
            "file": ""
        }
    }

If run with the previous configuration file this would yield the
following command line:

    app.exe -f -i in.txt -o out.txt -b file > C:/output/mycase/test1.log

###Custom interpolation
Three custom interpolation values are supported in test case files.
 - $(datetime) will be replaced by current date-time in the
        the format YYYYMMDD_HHMMSS
 - $(outdir) will be replaced by current test set output
        directory
 - $(outsubdir) will be replaced by current test case output
        sub-directory

USAGE
================================================================================

To display a full listing of the application options use the --help flag.

    ./clitestbed.py [--dry-run] [--help] <configuration file>

REQUIREMENTS
================================================================================

    >= Python 2.7.8

LICENSE
================================================================================

Copyright (c) 2014 Daniel Pulido <dpmcmlxxvi@gmail.com>

clitestbed is released under the [MIT License](http://opensource.org/licenses/MIT)

CHANGELOG
================================================================================

- Version 0.1.0
    
  * Initial release

AUTHOR
================================================================================

Copyright 2014 by Daniel Pulido <dpmcmlxxvi@gmail.com>

