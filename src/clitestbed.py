#!/usr/bin/env python
"""
File

    clitestbed.py

Description

    The Command Line Test Bed (clitestbed) runs a set of tests on a
    command line application and generates a summary report of the
    test pass/fail performance.

    The Test Bed runs a collection of Test Sets where each
    Test Set contains multiple Test Cases. Both the Test Sets
    and Test Cases are defined by JSON configuration files.
    See below for their format.

Usage

    clitestbed.py [--dry-run] <configuration file>

Return value

    0 = Success
    1 = Failed argument parsing
    2 = Failed running testbed

Test Set configuration file

    See documentation.

Test Case argument file

    See documentation.

Author

    Report bugs to dpmcmlxxvi@gmail.com

"""

import collections
import glob
import json
import logging
import os
import platform
import subprocess
import sys
import time

from optparse import OptionParser

class ApplicationProperties:
    """
    Application Properties
    """

    AUTHOR = "dpmcmlxxvi@gmail.com"
    DESCRIPTION = """Command Line Test Bed (clitestbed) is an application to
                    run a set of tests on a command line application and
                    generate a summary report of the test pass/fail performance.
                    """
    NAME = "clitestbed"
    VERSION_MAJOR = "0"
    VERSION_MINOR = "1"
    VERSION_PATCH = "0"

    @staticmethod
    def author():
        return ApplicationProperties.AUTHOR

    @staticmethod
    def description():
        return ApplicationProperties.DESCRIPTION

    @staticmethod
    def name():
        return ApplicationProperties.NAME

    @staticmethod
    def version():
        return (ApplicationProperties.VERSION_MAJOR + "." +
                ApplicationProperties.VERSION_MINOR + "." +
                ApplicationProperties.VERSION_PATCH)

def assignOrder(order):
    """
    Static method that adds the order attribute to a function.  
    :param order: Order in which the function will be called
    """
    def dstFunc(srcFunc):
        srcFunc.order = order
        return srcFunc
    return dstFunc

def checkFileIsExecutable(program):
    """
    Check that the input filename is executable. The file path
    as well as the system path are checked.
    :param program: File to check
    """
    def isExecutable(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fnorm = os.path.normpath(program)
    fpath = os.path.dirname(fnorm)
    if len(fpath):
        # If file path provided then check file
        if isExecutable(program):
            return True
    else:
        # Iterate through directories in PATH and check file
        for path in os.environ["PATH"].split(os.pathsep):
            fpath = os.path.join(path, program)
            if isExecutable(fpath):
                return True

    return False

def checkFileIsWritable(filename, create=False):
    """
    Check that the input filename is writable. That is, the path
    leading up to it exists and you can write to it. If it doesn't
    exists the needed folders can be created.
    :param file: File to check
    :param create: If True then needed directories are created
    """
    try:

        if filename is None:
            return False

        # Don't bother if the file already exists
        if (os.path.isfile(filename)):
            return True;

        # If it's an existing directory then can't create
        if (os.path.isdir(filename)):
            return False;

        # Get file directory
        filedir = os.path.dirname(filename)

        # If directory exists then just create the file
        if (os.path.isdir(filedir)):
            return True

        # Create needed directories and file
        if create:
            os.makedirs(filedir)

    except:

        return False

    return True

def createTimeStampFolderName(srcTime=None):
    """
    Convert time structure to a string for creating a time stamped
    folder or filename: YYYYMMDD_HHMMSS. If no source time is provided
    then the current time is used.
    :param srcTime: Time in struct_time format (e.g. from time.localtime())
    """
    if srcTime is None:
        time.strftime('%Y%m%d_%H%M%S', time.localtime())
    else:
        time.strftime('%Y%m%d_%H%M%S', srcTime)

def normalizePath(srcPath):
    """
    Normalize path to current OS
    Currently only cygwin requires conversion
    """
    if platform.system().lower().find("cygwin") >= 0:
        stdoutp=os.popen("cygpath " + repr(srcPath))
        dstPath=stdoutp.read().strip()
        return dstPath
    return srcPath

class CommandLineArgument:
    """
    Class that defines a command line argument
    """
    def __init__(self, option="", value=""):
        """
        Create a command line argument
        :param option: Argument option (e.g., -v)
        :param value: Argument value (e.g., 1)
        """
        self.option = option
        self.value = value

    def getOption(self):
        """
        Access argument option
        """
        return self.option

    def getValue(self):
        """
        Access argument option
        """
        return self.value

class CommandLineParser:
    """
    Class to parse command line arguments
    """
    USAGE="usage: %prog [--help] <configuration file>"

    def __init__(self):

        self.good = False
        self.config = None
        self.dryrun = False
        self.parser = OptionParser(
            description=ApplicationProperties.description(),
            usage=CommandLineParser.USAGE,
            version=ApplicationProperties.version())
        self.parser.add_option("--dry-run",
                               action="store_true",
                               dest="dryrun",
                               default=False,
                               help="prints command line without executing it.")

    def getConfig(self):
        return self.config

    def isDryrun(self):
        return self.dryrun

    def isGood(self):
        return self.good

    def parse(self):

        (options, args) = self.parser.parse_args()

        if len(args) == 0:
            self.parser.print_usage()
            return

        if len(args) != 1:
            self.parser.error("incorrect number of arguments")
            return

        self.dryrun = options.dryrun
        self.config = args[0]
        self.good = True

class FileHandler:
    """
    Simple file handle wrapper to clean up resources when done.
    Should be used with the "with" syntax to ensure clean up.
    """

    def __init__(self, filename, mode):
        self.handle = open(filename, mode)

    def __del__(self):
        self.handle.close()

    def getHandle(self):
        return self.handle

class TestBedInterpolator:
    """
    Interpolates for testbed interpolants
    """
    outdir=os.getcwd()
    outsubdir=""

    def __init__(self):
        pass

    def setOutdir(self, outdir):
        """
        :param outdir: Output directory
        """
        self.outdir = outdir

    def setOutSubdir(self, outsubdir):
        """
        :param outsubdir: Output sub-directory
        """
        self.outsubdir = outsubdir

    @assignOrder(1)
    def interpolateDateTime(self, expression):
        """
        Interpolate for date-time string $(datetime) with current 
        date-time stamp in YYYYMMDD_HHMMSS format
        :param expression: Source expression to search and replace for date/time
        """
        pattern = "$(datetime)"
        value = time.strftime('%Y%m%d_%H%M%S', TestBedConfigParser.currentTime)
        return expression.replace(pattern,value)

    @assignOrder(2)
    def interpolateOutdir(self, expression):
        """
        Interpolate for output directory string $(outdir) with default directory 
        :param expression: Source expression to search and replace for directory
        """
        pattern = "$(outdir)"
        value = self.outdir
        return expression.replace(pattern,value)

    @assignOrder(3)
    def interpolateOutsubdir(self, expression):
        """
        Interpolate for output directory string $(outdir) with default directory 
        :param expression: Source expression to search and replace for directory
        """
        pattern = "$(outsubdir)"
        value = self.outsubdir
        return expression.replace(pattern,value)

    def interpolate(self, expression):
        """
        Interpolate source expression with all TestBed patterns  
        :param expression: Source expression to search and replace with patterns
        """

        # get a list of fields that have the order set and sort them by order
        methods = sorted( [ getattr(self, field) for field in dir(self) 
                           if hasattr(getattr(self, field), "order") ],
                           key = (lambda field: field.order) )
        for method in methods:
            expression = method(expression)
        return expression

class TestBedConfigParser():
    """
    Custom TestBed configuration parser
    """

    # ========================================
    # Members
    # ========================================
    interpolator = TestBedInterpolator()
    currentTime = time.localtime()

    def __init__(self):
        self.data = {}

    def has_option(self, section, option):
        """
        Check if given section has option
        :param section: Configuration section
        :param option: Configuration section option
        """
        if (not self.data.has_key(section)): return False
        if (not self.data[section].has_key(option)): return False
        return True

    def parseOption(self, section, option):
        """
        Parse the input section option and interpolates any matching patterns.
        If pattern matching is not desired then use get()
        :param section: Configuration section
        :param option: Section option
        :return: Interpolated option value
        """
        node = self.data[section]
        expression = node[option]
        if (type(expression) is list):
            for i in range(len(expression)):
                expression[i] = self.interpolator.interpolate(expression[i])
            return expression
        return self.interpolator.interpolate(expression)

    def parseItemValues(self, section):
        """
        Parse the input section item values and interpolate matching patterns.
        If pattern matching is not desired then use items()
        :param section: Configuration section
        :returns: Interpolated option items
        """
        node = self.data[section]
        pairs = node.iteritems()
        result = []
        for item in pairs:
            result.append((self.interpolator.interpolate(item[0]),
                           self.interpolator.interpolate(item[1])))
        return result

    def read(self, filename):
        """
        Read configuration file
        :param filename: Configuration filename
        """
        try:
            with open(filename, 'r') as f:
                self.data = json.load(f, object_pairs_hook=collections.OrderedDict)
        except:
            raise Exception("Unable to read configuration file")

    def sections(self):
        """
        Configuration file sections
        :returns: Top level section
        """
        return self.data.keys()

class TestCase:
    """
    Class that defines a Test Case
    """

    # ========================================
    # SECTION: TEST
    # ========================================
    SECTION_TEST="TEST"
    PROP_TEST_DESCRIPTION="DESCRIPTION"
    PROP_TEST_OUTSUBDIR="OUTSUBDIR"
    PROP_TEST_LOGFILE="LOGFILE"

    # ========================================
    # SECTION: ARGUMENTS
    # ========================================
    SECTION_ARGS="ARGUMENTS"

    def __init__(self, configFile, description, outsubdir, logfile, arguments):
        """
        :param configFile: Test configuration file
        :param description: Test case description
        :param outsubdir: Output sub directory
        :param logfile: Output log file
        :param arguments: List of command line arguments
        """
        self.configFile = configFile
        self.description = description
        self.outsubdir = outsubdir
        self.logfile = logfile
        self.arguments = arguments

        # Initialize derived properties: logger, etc.
        self.initialize()

    def getConfigFile(self):
        """
        Access case configuration file
        :returns: TestCase configuration file
        """
        return self.configFile

    def initialize(self):

        # Create logger        
        self.logger = logging.getLogger(self.configFile)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s: %(levelname)10s: %(message)s',
            '%Y-%m-%d %H:%M:%S')

        # Add console handler to logger
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
        self.logger.addHandler(consoleHandler)

    def run(self, executable, outdir, environment=None, dryrun = False):
        """
        Run test case
        """
        # Build command line
        command = [executable]
        for argument in self.arguments:
            if len(argument.getOption()) > 0:
                command = command + [argument.getOption()]
            if len(argument.getValue()) > 0:
                command = command + [argument.getValue()]

        tStart = time.time()

        if dryrun:

            # Perform dry-run by printing would be command
            self.logger.info("Dry run command: %s" % ' '.join(command))
            status = 0

        else:

            try:

                # Get executable path
                exedir = os.path.dirname(executable)
                if len(exedir.strip()) == 0:
                    exedir = os.getcwd()

                # Make sure log file exists
                testLogFileToWrite = os.path.normpath(
                    os.path.join(outdir, self.outsubdir, self.logfile))
                testLogCreated = checkFileIsWritable(testLogFileToWrite, True)
                if (testLogCreated is False):

                    self.logger.critical("Log file is not writable: " +
                                         testLogFileToWrite)
                    return -1;

                # Run command as a subprocess
                testLogHandle = FileHandler(testLogFileToWrite,'w')
                process = subprocess.Popen(command,
                                           stdout=testLogHandle.getHandle(),
                                           stderr=testLogHandle.getHandle(),
                                           env=environment,
                                           cwd=exedir)
                status = process.wait()

            except Exception, e:
                message = "Exception occurred launching application: %s" % e
                self.logger.critical(message)
                self.logger.critical("Stopping test case.")
                return -2

        tElapsed = time.time() - tStart;
        self.logger.info("Test Case elapsed time (seconds): %i" % tElapsed)

        return status

    def printSettings(self):
        """
        Print settings to logger
        """

        fmt = "%15s: %s"

        self.logger.info(fmt, "TEST CASE", self.configFile)
        self.logger.info(fmt, "DESCRIPTION", self.description)
        self.logger.info(fmt, "OUTSUBDIR", self.outsubdir)
        self.logger.info(fmt, "LOG FILE", self.logfile)

        for case, argument in enumerate(self.arguments):
            self.logger.info(fmt,
                             "ARGUMENT #" + str(case),
                             argument.option + " " + argument.value)

        return

    def setLogger(self, logger):
        """
        Set test case logger. Default is console
        """
        self.logger = logger

    @staticmethod
    def createTestCase(outdir, configFile):
        """
        Create a Test Case in a configuration file
        :param outdir: Test set output directory
        :param configFile: Test case configuration filename
        """

        # Create parser
        config = TestBedConfigParser()
        config.interpolator.setOutdir(outdir)
        config.optionxform = str
        config.read(configFile)

        # Extract test properties
        outsubdir=config.parseOption(
            TestCase.SECTION_TEST,
            TestCase.PROP_TEST_OUTSUBDIR)
        config.interpolator.setOutSubdir(outsubdir)
        description=config.parseOption(
            TestCase.SECTION_TEST,
            TestCase.PROP_TEST_DESCRIPTION)
        logfile=config.parseOption(TestCase.SECTION_TEST,
                                   TestCase.PROP_TEST_LOGFILE)
        args=config.parseItemValues(TestCase.SECTION_ARGS)

        arguments = []
        for argument in args:
            clarg = [CommandLineArgument(argument[0],argument[1])]
            arguments = arguments + clarg

        return TestCase(configFile,
                        description,
                        outsubdir,
                        logfile,
                        arguments)

class TestSet:
    """
    A collection of Test Cases for a single executable.
    """

    # ========================================
    # SECTION PROPERTIES
    # ========================================
    PROP_GROUP_EXECUTABLE="EXECUTABLE"
    PROP_GROUP_SUCCESSCODE="SUCCESSCODE"
    PROP_GROUP_TESTDIR="TESTDIR"
    PROP_GROUP_TESTCASES="TESTCASES"
    PROP_GROUP_OUTDIR="OUTDIR"
    PROP_GROUP_PATHDIRS="PATHDIRS"
    PROP_GROUP_LOGFILE="LOGFILE"
    PROP_GROUP_LOGLEVEL="LOGLEVEL"

    # ========================================
    # DEFAULT PROPERTIES
    # ========================================
    PROP_GROUP_SUCCESSCODE_DEFAULT=0
    PROP_GROUP_LOGLEVEL_DEFAULT="DEBUG"

    # ========================================
    # CONFIGURATION EXTENSIONS
    # ========================================
    CONFIG_EXTENSION=".json"

    def __init__(self,
                 name,
                 executable,
                 successCode,
                 outdir,
                 cases,
                 pathdirs=None,
                 logfile=None,
                 loglevel=None):
        """
        :param name: Set name
        :param executable: Set executable path
        :param executable: Set executable succes return code
        :param outdir: Output directory
        :param cases: Test case files to be run for this Set
        :param pathdirs: Optional list of directories to add to system path
        :param environment: OS Environment to run Test Cases
        :param logger: Log file to write test results
        """
        self.name = name
        self.executable = executable
        self.successCode = successCode
        self.outdir = outdir
        self.cases = cases
        self.pathdirs = pathdirs
        self.logfile = logfile
        self.loglevel = loglevel

        self.logger = None
        self.loggerHandler = None
        self.environment = None

        # Initialize derived properties: logger, system environment, etc.
        self.initialize()

    def __del__ (self):
    
        # Clean up handler
        if self.loggerHandler is not None:
            self.logger.removeHandler(self.loggerHandler)
            self.loggerHandler.close()

    def initialize(self):

        # Build log file path
        logFilePath = None
        logFileValid = self.logfile is not None
        if logFileValid:
            logFilePath = os.path.normpath(os.path.join(self.outdir,
                                                        self.logfile))
            logFileValid = checkFileIsWritable(logFilePath, True)

        # Extract log level
        logNumericLevel = getattr(logging, self.loglevel.upper(), None)
        isLogLevelValid = isinstance(logNumericLevel, int)
        if not isLogLevelValid:
            logNumericLevel = getattr(logging,
                                      TestSet.PROP_GROUP_LOGLEVEL_DEFAULT,
                                      None)

        # Create logger        
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logNumericLevel)
        formatter = logging.Formatter(
            '%(asctime)s: %(levelname)10s: %(message)s',
            '%Y-%m-%d %H:%M:%S')

        # Add console handler to logger
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
        self.logger.addHandler(consoleHandler)

        # Add file handler to logger
        try:
            if logFileValid:
                self.loggerHandler = logging.FileHandler(normalizePath(
                    os.path.normpath(logFilePath)))
                self.loggerHandler.setFormatter(formatter)
                self.logger.addHandler(self.loggerHandler)
        except:
            self.logger.critical("Unable to create file logger: " + logFilePath)

        # Warn user about logger failures
        if not logFileValid:
            self.logger.critical(('Invalid log file: %s' % logFilePath))

        if not isLogLevelValid:
            self.logger.critical(('Invalid log level: %s' % self.loglevel))
            self.logger.critical("Setting log level to " +
                                 TestSet.PROP_GROUP_LOGLEVEL_DEFAULT)

        # Modify test set system environment
        if self.pathdirs is not None:
            self.environment = os.environ.copy()
            for pathdir in self.pathdirs:
                self.environment["PATH"] = (os.path.normpath(pathdir) +
                                            os.pathsep +
                                            self.environment["PATH"])

    def printSettings(self):
        """
        Print settings to logger
        """

        fmt = "%10s: %s"

        self.logger.info(fmt, "TEST SET", self.name)
        self.logger.info(fmt, "EXECUTABLE", self.executable)
        self.logger.info(fmt, "OUTPUT DIR", self.outdir)

        for index, case in enumerate(self.cases):
            caseFile = "None"
            if case is not None:
                caseFile = case.getConfigFile()
            self.logger.info(fmt, "CASE #" + str(index+1), caseFile)

        for pathdir in self.pathdirs:
            self.logger.info(fmt, "PATHDIRS", pathdir)

        return

    def run(self, dryrun = False):
        """
        Run Test Set cases
        """

        self.logger.info("========================================")
        self.printSettings()

        numTest = 0
        numPass = 0
        for caseIndex, case in enumerate(self.cases):

            numTest += 1

            self.logger.info("----------------------------------------")
            self.logger.info("Running CASE # " + str(caseIndex+1))

            if not case:
                self.logger.error("No test case found. Skipping.")
                continue

            # Write case options
            case.setLogger(self.logger)
            case.printSettings()

            # Run test case
            try:
                status = case.run(self.executable,
                                  self.outdir,
                                  self.environment,
                                  dryrun)
                if dryrun:
                    status = self.successCode

                if (status == self.successCode):
                    numPass+=1
            except:
                status = None
                self.logger.critical("An unhandled exception occurred when " +
                                     "running case. Skipping.")

            if status == self.successCode:
                self.logger.info("Test Case return status: %i" % status)
            else:
                self.logger.error("Test Case return status: %i" % status)

        numFail = numTest-numPass
        self.logger.info("----------------------------------------")
        self.logger.info("TOTAL NUMBER OF TESTS: " + str(numTest))
        self.logger.info("TOTAL NUMBER OF PASS: " + str(numPass))
        self.logger.info("TOTAL NUMBER OF FAIL: " + str(numFail))

        return numFail

    @staticmethod
    def createTestSet(configFile, section):
        """
        Create a new Test Set
        :param configFile: Configuration filename
        :param section: Name of test Set to extract to extract
        """

        # Create parser
        config = TestBedConfigParser()
        config.optionxform = str
        config.read(configFile)

        # Extract executable path
        exePath = config.parseOption(section, TestSet.PROP_GROUP_EXECUTABLE)

        # Extract success code
        successCode = TestSet.PROP_GROUP_SUCCESSCODE_DEFAULT
        if config.has_option(section, TestSet.PROP_GROUP_SUCCESSCODE):
            successCode = config.parseOption(section,
                                             TestSet.PROP_GROUP_SUCCESSCODE)

        # Extract output directory
        outDir = config.parseOption(section, TestSet.PROP_GROUP_OUTDIR)
        config.interpolator.setOutdir(outDir)

        # Extract test files by concatenating
        testFiles = []

        if config.has_option(section, TestSet.PROP_GROUP_TESTDIR):
            testDir = config.parseOption(section, TestSet.PROP_GROUP_TESTDIR)
            globStr = (testDir.replace('"','') +
                       os.path.sep +
                       "*" +
                       TestSet.CONFIG_EXTENSION)
            testDirFiles = glob.glob(globStr)
            testFiles = testFiles + testDirFiles

        if config.has_option(section, TestSet.PROP_GROUP_TESTCASES):
            testCases = config.parseOption(section,TestSet.PROP_GROUP_TESTCASES)
            testFiles = testFiles + testCases

        if len(testFiles)==0:
            raise Exception("Configuration file missing test cases")

        # Create test cases
        cases = []
        for testFile in testFiles:
            try:
                case = TestCase.createTestCase(outDir, testFile)
                if case: cases.append(case)
            except Exception as e:
                print "Error: {}".format(e)
                print "Skipping test case {} from {}. Skipping.".format(
                    testFile,
                    configFile)

        # Extract environment path directories
        pathdirs = []
        if config.has_option(section, TestSet.PROP_GROUP_PATHDIRS):
            pathdir = config.parseOption(section, TestSet.PROP_GROUP_PATHDIRS)
            pathdirs = pathdirs + pathdir.split('\n')

        # Extract log file
        logFile = None
        if config.has_option(section, TestSet.PROP_GROUP_LOGFILE):
            logFile = config.parseOption(section, TestSet.PROP_GROUP_LOGFILE)

        # Extract log level
        logLevel = TestSet.PROP_GROUP_LOGLEVEL_DEFAULT
        if config.has_option(section, TestSet.PROP_GROUP_LOGLEVEL):
            logLevel = config.parseOption(section, TestSet.PROP_GROUP_LOGLEVEL)

        return TestSet(section,
                       exePath,
                       successCode,
                       outDir,
                       cases,
                       pathdirs,
                       logFile,
                       logLevel)

    @staticmethod
    def createTestSets(configFile):
        """
        Create a list of all Test Sets in a configuration file
        :param configFile: Configuration filename
        """

        # Create parser
        config = TestBedConfigParser()
        config.read(configFile)

        # Extract all sections in configuration file
        sections = config.sections()
        if (len(sections) == 0):
            raise Exception("No test sets sections in configuration file")

        # Parse all sets in configuration file
        sets = []
        for section in sections:
            try:
                testset = TestSet.createTestSet(configFile, section)
                if testset: sets.append(testset)
            except Exception as e:
                print "Error: {}".format(e)
                print "Skipping section {} from {}. Skipping.".format(
                    section,
                    configFile)

        if (len(sets) == 0):
            raise Exception("No test sets created in configuration file")

        return sets

def clitestbed(configFile, dryRun=False):
    """
    Test Bed
    :param configFile: Configuration file
    :param dryRun: True if performing a dry run otherwise False
    :returns: Number of failed tests
    """

    # Load test sets
    tests = TestSet.createTestSets(configFile)

    # Run each test set
    numFailTotal = 0
    for test in tests:

        numFail = test.run(dryRun)
        numFailTotal += numFail

    return numFailTotal

def main(argv=None):
    """
    Command line main function
    :param argv: Command line arguments
    """

    # Parser command line arguments
    parser = CommandLineParser()
    parser.parse()
    if not parser.isGood():
        return 1

    configFile = parser.getConfig()
    dryRun = parser.isDryrun()

    # Load test sets
    try:
        clitestbed(configFile, dryRun)
    except Exception as e:
        print "Error: {}".format(e)
        print "Exiting"
        return 2

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
