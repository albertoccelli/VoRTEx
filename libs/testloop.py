# TODO merge common tests and Natural Language ones

# default libraries
import os
# user interface
import tkinter as tk
from datetime import datetime
from tkinter import filedialog
from msvcrt import getch
from .Server.server import send_message

import random
import numpy as np
from scipy.io.wavfile import read, write

from .ABC_weighting import a_weight
# custom libraries
from .dsp import get_rms, add_gain, SaturationError
from .configure import load_list
from .play import play_data
from .recorder import Recorder
from .cli_tools import print_square, clear_console, show_image
from . import metadata
from threading import Thread
from .Server.server import open_connection, send_message

root = tk.Tk()
root.wm_attributes("-topmost", 1)
root.withdraw()

cPath = os.getcwd()

langDict = {"ARW": "Arabic",
            "CHC": "Chinese",
            "DUN": "Dutch",
            "ENG": "English (UK)",
            "ENA": "English (Australia)",
            "ENI": "English (India)",
            "ENU": "English (USA)",
            "FRF": "French (France)",
            "FRC": "French (Canada)",
            "GED": "German",
            "GED_NLU": "German (Natural language)",
            "ITA": "Italian",
            "ITA_NLU": "Italian (Natural language)",
            "JPJ": "Japanese",
            "KRK": "Korean",
            "PLP": "Polish",
            "PTP": "Portuguese (Portugal)",
            "PTB": "Portuguese (Brazil)",
            "RUR": "Russian",
            "SPE": "Spanish (Spain)",
            "SPM": "Spanish (Mexico)",
            "TRT": "Turkish"
            }

nonsense = ["Collecting shells...", "Parkouring...", "Harvesting potatoes...", "Eating sugar", "Holding beers...",
            "Destroying the Death Star", "Learning Kung Fu...", "Fixing the time machine", "Unboxing cats...",
            "Parking Millennium Falcon..."]


class CorruptedTestError(Exception):
    pass


class TestExistsError(Exception):
    pass


def sort_dict(dictionary):
    keys = []
    for i in list(dictionary.keys()):
        keys.append(int(i))
    keys.sort()
    new_dict = {}
    for i in keys:
        new_dict[str(i)] = dictionary[str(i)]
    return new_dict


def _abs_to_rel(path):
    """
    Convert path from absolute to relative
    """
    cwd = os.getcwd().replace("\\", "/")
    return path.split(cwd)[-1]


def splash():
    clear_console()
    show_image("./utilities/logo.txt")
    welcome = "VoRTEx %s - Voice Recognition Test Execution\n" \
              "%s\n" \
              "\n" \
              "Os: %s\n" \
              "%s\n" \
              "email: %s\n" \
              "%s" % (metadata["version"], metadata["description_short"], metadata["os"], metadata["copyright"],
                      metadata["email"], metadata["url"])
    print_square(welcome, margin=[20, 20, 1, 1], centering="center")
    return


def clr_tmp():
    try:
        os.remove("temp.wav")
    except FileNotFoundError:
        pass
    return


def now():
    """
    Returns the current date and time.
    """
    now_time = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    return now_time


def log(event, log_name="test_status.log", log_time=None):
    """
    Log every test event with a timestamp.
    """
    print("Logging into %s" % log_name)
    if log_time is None:
        log_time = now()
    with open(log_name, "a", encoding="utf-16") as r:
        r.write(log_time + "\t")
        r.write(event + "\n")
    #send_message(log_time + "\t" + event)
    return


def show_dirs(path):
    directories = []
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            directories.append(name)
    return directories


# noinspection SpellCheckingInspection
def lombard(noise):
    """
    The noise is expressed in dBA
    """
    if 50 <= noise <= 77:
        lombard_gain = (8 / 27) * (noise - 50)
    elif noise > 77:
        lombard_gain = 8
    else:
        lombard_gain = 0
    return np.round(lombard_gain, 3)


# noinspection SpellCheckingInspection
class Test:

    def __init__(self):
        # declare the attributes of the test
        self.testName = ""  # The name of the test
        self.wPath = "."  # The current working path of the selected test
        self.settingsDir = "settings/"  # the directory for the settings of the program
        self.settingsFile = "settings/settings.vcfg"  # the settings file
        self.databaseDir = "database/"  # the directory of the testlist databases
        self.logname = ""  # path of the log file
        self.report_file = ""  # path of the csv
        self.testDir = "vr_tests/"  # Where all the tests are contained
        self.phrasesPath = "phrases/"  # The path of the audio files
        self.testfile = ""
        self.listfile = ""
        # status of the test (default values)
        self.lang = "ITA"  # The language used for the test (to be defined during the test configuration)
        self.isMultigenderEnabled = False
        self.gender = None
        self.isNluEnabled = True  # Is Natural Language enabled?
        self.mic_mode = 2  # how the infotainment microphone is activated: ptt(1), wakeword(2), can message(3)
        self.issued_ww = 0  # How many times has the wakeword been pronounced
        self.recognized_ww = 0  # How many times has the wakeword been recognized
        self.passes = 0  # How many passes are there?
        self.failed = []  # List of failed tests
        self.status = 0  # Is the test running? (0: waiting; 1: running; 2: completed)
        self.current_test = 0  # The test number we should start from. If the test is new, then the status is 0.
        self.results = {}  # A list containing the test results
        self.isMouthCalibrated = False  # Is the mouth calibrated?
        self.gain = 0  # The gain value for the mouth to reach 94dBSPL
        self.isLombardEnabled = True
        self.noise = 0  # RMS value of the background noise
        self.noise_radio = 0  # RMS value of the background noise plus the radio on
        self.testlist = []
        self.redo = []
        # self.testlist = [0, 1, 9, 32, 33, 37, 38, 39, 41, 42, 43, 49, 50, 54, 55, 58, 86, 87,
        #                 91, 92, 94, 103, 104, 128, 129, 131, 134, 136, 138, 139, 146, 152]
        self.database = {}
        self.isFirstStart = False
        self.isSaved = True
        # open the sound recorder for calibration and translation
        print("------------------------------------------------------------------")
        print("Opening sound recorder\n")
        # Audio device settings
        self.recorder = Recorder()
        print("\nChannels: %d\n" % self.recorder.channels)
        self.recorder.channels = 2  # set 2 channels
        # channel assignment
        # output
        self.mouthChannel = 0
        self.noiseChannel = 1
        # input
        self.micChannel = 0
        self.earChannel = 1
        #self.is_online = False
        #try:
        #    open_connection("10.38.103.82", 42424)
        #    self.is_online = True
        #except ConnectionRefusedError:
        #    print("Connection refused by target machine. Continuing offline...")
        #except Exception as e:
        #    print("Error %s;\n Continuing offline..." % e)
        #  Internet connection
        self.ip, self.port = open_connection(42886)

        print("------------------------------------------------------------------")

    def log(self, event, log_name="test_status.log", log_time=None):
        """
        Log every test event with a timestamp.
        """
        print("Logging into %s" % log_name)
        if log_time is None:
            log_time = now()
        with open(log_name, "a", encoding="utf-16") as r:
            r.write(log_time + "\t")
            r.write(event + "\n")
        #send_message(log_time + "\t" + event + "\n")
        #if self.is_online:
            #try:
            #    send_message(log_time + "\t" + event)
            #except Exception as e:
            #    print("Error %e. Now offline!" % e)
            #    self.is_online = False
        return


    def load_database(self, database_file=None):
        # select the proper list file with the command lists
        if database_file is None:
            database_file = filedialog.askopenfilename(title="Choose the list file for the test",
                                                       filetypes=[("Voice Recognition Test List files", "*.vrtl"),
                                                                  ("All files", "*")],
                                                       initialdir=self.databaseDir)
            if not database_file:
                return
        try:
            self.listfile = _abs_to_rel(database_file)
            self._configure_list()  # get the command database (languages, lists) from the list file
        except PermissionError:
            print("No file chosen!")
        return


    def _configure_list(self):
        """
        Detects the available language and the number of tests for language

        Opens the database file and converts it into a dictionary form suitable for the test.

        test = {"LANG1" = [[], [], [], []],
                "LANG2" = [[], [], [], []],
                ecc...
                }
        """
        self.database = load_list(
            os.getcwd().replace("\\", "/") + self.listfile)  # create the test sequence dictionary from the vrtl file
        self.langs = []  # list of the currently supported languages
        for k in self.database.keys():
            if k != "preconditions" and k != "expected" and k != "AUDIOPATH" and "WEIGHTS" not in k:
                self.langs.append(k)
        self.langs.sort()
        return

    def new(self, testname=None, l_index=None, gender=0, testlist=None):
        # decide the name of the test
        self.testName = testname
        # create a new folder based on the test
        self.wPath = "%s%s" % (self.testDir, self.testName)  # this will be your new working directory
        try:
            os.mkdir(self.wPath)  # create a new directory for the test
        except FileExistsError:
            raise TestExistsError()
        # create the configuration file
        self.logname = "%s/testlog.log" % self.wPath
        self.testfile = "%s/config.cfg" % self.wPath
        # decide the language
        if l_index is not None:
            self.lang = self.langs[l_index]
        try:  # if available, imports the array for the preconditions and expected behaviour
            self.expected = self.database["expected"]
        except KeyError:
            pass
        try:
            self.preconditions = self.database["preconditions"]
        except KeyError:
            pass
        self.sequence = self.database[self.lang]
        # detects whether male and female voices are available
        langpath = self.lang
        g = 0
        for i in os.listdir(self.database["AUDIOPATH"]):
            if self.lang in i:
                g += 1
        if g == 2:
            if gender == 1:
                langpath = self.lang + "_M"
            elif gender == 0:
                langpath = self.lang + "_F"

        if len(self.database[self.lang]) > 157:  # detects if natural language is available
            self.isNluEnabled = True
        else:
            self.isNluEnabled = False
        self.phrasesPath = self.database["AUDIOPATH"] + langpath  # build the path for the speech files
        self.save()  # save the configuration into the cfg file
        # reset status values
        self.current_test = 1
        self.issued_ww = 0  # How many times has the wakeword been pronounced
        self.recognized_ww = 0  # How many times has the wakeword been recognized
        self.passes = 0  # How many passes are there?
        self.failed = []  # List of failed tests
        self.status = 0  # Is the test running?
        self.current_test = 0  # The test number we should start from. If the test is new, then the status is 0.
        print_square("Creating test (%s)\n\n"
                     ""
                     "Language: %s\n"
                     "Testlist: %s\n"
                     "Status: %s" % (self.wPath, self.lang, self.testlist, self.status))
        self.results = {}  # A list containing the test results
        self.isSaved = True
        if testlist is None:
            self.testlist = range(len(self.database[self.lang]))
        else:
            self.testlist = testlist
        return

    def resume(self, path=None):
        if path is not None:
            self.wPath = path
        self.testfile = "%s/config.cfg" % self.wPath  # the configuration file's path
        self.load_conf()  # retrieve the paths and test status from the configuration file
        self._configure_list()  # get the test configuration (languages, lists) from the listfile
        self.save()
        self.log("Hi there! Resuming test...", self.logname)
        return

    def detectgenders(self, lang):
        """
        For the selected language, detects if both male and female voice are available,
        based on the folders on the "phrases" directory.
        """
        path = self.phrasesPath
        languages = []
        for i in os.listdir(path):
            if lang in i:
                languages.append(i)
        return len(languages)

    def getstatus(self):
        # print the status of the test and ask for confirmation
        while True:
            print_square("LANGUAGE: %s\n"
                         "RUNNING: %s\n"
                         "STATUS: %s/%s" % (self.lang, self.status, self.current_test,
                                            len(self.database[self.lang])),
                         margin=[5, 5, 1, 1],
                         title="TEST STATUS")
            try:
                if self.status:
                    input("Do you want to continue with this test? (ENTER to continue, CTRL+C to cancel and choose "
                          "another one) ")
                else:
                    input("Press ENTER to continue")
                break
            except KeyboardInterrupt:
                self.resume()

    # save and load functions
    def save(self):
        self.save_settings()
        self.save_conf()
        self.isSaved = True

    def save_conf(self, testfile=None):
        """
        Writes the test attributes (including the current progress) into the config file, along with information
        regarding the .vrtl file used for the single test. Overwrites the last.vcfg file in the settings folder
        """
        #print_square("SAVING\n\nStatus: %s" % self.status)
        if testfile is None:
            testfile = self.testfile
        with open(testfile, "w", encoding="utf-16") as r:
            r.write("@YODA\n")
            r.write("@CONFIGURATION\n")
            r.write("WDIR=%s\n" % self.wPath)
            r.write("LISTFILE=%s\n" % self.listfile)
            r.write("LOG=%s\n" % self.logname)
            r.write("PHRASESPATH=%s\n" % self.phrasesPath)
            r.write("LANG=%s\n" % self.lang)
            r.write("NLU=%s\n" % self.isNluEnabled)
            r.write("MOUTH_CALIBRATED=%s\n" % self.isMouthCalibrated)
            r.write("MOUTH_CORRECTION=%s\n" % self.gain)
            r.write("MIC_CALIBRATED=%s\n" % self.recorder.calibrated)
            r.write("MIC_DBFSTODBSPL=%s\n" % self.recorder.correction)
            r.write("LOMBARD=%s\n" % self.isLombardEnabled)
            r.write("NOISE_RADIO_OFF=%s\n" % self.noise)
            r.write("NOISE_RADIO_ON=%s\n" % self.noise_radio)
            r.write("\n")
            # save progress
            r.write("@PROGRESS\n")
            r.write("TESTLIST=%s\n" % self.testlist)
            r.write("STARTED=%s\n" % self.status)
            r.write("STATUS=%s\n" % self.current_test)
            r.write("ISSUED_WW=%d\n" % self.issued_ww)
            r.write("RECOGNIZED_WW=%d\n" % self.recognized_ww)
            r.write("PASSED=%s\n" % self.passes)
            r.write("RESULTS=%s\n" % self.results)
        return

    def load_conf(self, testfile=None):
        """
        Reads the configuration file for the selected test
        """
        print("Loading test...")
        if testfile is None:
            testfile = self.testfile
        with open(testfile, "r", encoding="utf-16") as r:
            # CHECK INTEGRITY
            healthy = False
            for line in r.readlines():
                if "@YODA" in line:
                    healthy = True
        with open(testfile, "r", encoding="utf-16") as r:
            if healthy:
                for line in r.readlines():
                    # read configuration
                    if "STARTED" in line:
                        self.status = eval(line.split("=")[-1])
                    elif "STATUS" in line:
                        self.current_test = int(line.split("=")[-1])
                    elif "RESULTS" in line:
                        self.results = eval(line.split("=")[-1])
                    elif "LISTFILE" in line:
                        self.listfile = str(line.split("=")[-1].replace("\n", ""))
                    elif "PHRASESPATH" in line:
                        self.phrasesPath = str(line.split("=")[-1].replace("\n", ""))
                    elif "LANG" in line:
                        self.lang = str(line.split("=")[-1]).replace("\n", "")
                    elif "NLU" in line:
                        self.isNluEnabled = str(line.split("=")[-1]).replace("\n", "")
                    elif "ISSUED_WW" in line:
                        self.issued_ww = float(line.split("=")[-1].replace("\n", ""))
                    elif "RECOGNIZED_WW" in line:
                        self.recognized_ww = float(line.split("=")[-1].replace("\n", ""))
                    elif "WDIR" in line:
                        self.wPath = str(line.split("=")[-1].replace("\n", ""))
                    elif "LOG" in line:
                        self.logname = str(line.split("=")[-1].replace("\n", ""))
                    elif "PASSED" in line:
                        self.passes = int(line.split("=")[-1].replace("\n", ""))
                    elif "TESTLIST" in line:
                        self.testlist = eval(line.split("=")[-1].replace("\n", ""))

                self.testName = self.wPath.split("/")[-1]
                self._configure_list()
                try:  # if available, imports the array for the preconditions and expected behaviour
                    self.expected = self.database["expected"]
                except KeyError:
                    pass
                try:
                    self.preconditions = self.database["preconditions"]
                except KeyError:
                    pass
                print_square("Status: %s" % self.status)
                self.sequence = self.database[self.lang]
            else:
                print_square("!!! CONFIGURATION FILE CORRUPTED", centering="center")
            self.isSaved = True

    # settings functions
    def save_settings(self):
        """
        Save the settings file of the program into a .vcfg file
        """
        print("VoRTEx settings saved!")
        with open(self.settingsFile, "w", encoding="utf-16") as f:
            f.write("@YODA\n")
            f.write("@SETTINGS\n")
            f.write("LAST=%s\n" % self.wPath)
            f.write("MOUTH_CALIBRATED=%s\n" % self.isMouthCalibrated)
            f.write("MOUTH_CORRECTION=%s\n" % self.gain)
            f.write("MIC_CALIBRATED=%s\n" % self.recorder.calibrated)
            f.write("MIC_DBFSTODBSPL=%s\n" % self.recorder.correction)
            f.write("MIC_MODE=%s\n" % self.mic_mode)
            f.write("LOMBARD=%s\n" % self.isLombardEnabled)
            f.write("NOISE_RADIO_OFF=%s\n" % self.noise)
            f.write("NOISE_RADIO_ON=%s\n" % self.noise_radio)
        return

    def load_settings(self):
        """
        Load saved settings
        """
        try:
            with open(self.settingsFile, "r", encoding="utf-16") as f:
                for line in f.readlines():
                    if "MOUTH_CALIBRATED" in line:
                        self.isMouthCalibrated = eval(line.split("=")[-1])
                    elif "MOUTH_CORRECTION" in line:
                        self.gain = eval(line.split("=")[-1])
                    elif "MIC_CALIBRATED" in line:
                        self.recorder.calibrated = eval(line.split("=")[-1])
                    elif "MIC_DBFSTODBSPL" in line:
                        self.recorder.correction = eval(line.split("=")[-1])
                    elif "MIC_MODE" in line:
                        self.mic_mode = eval(line.split("=")[-1])
                    elif "LOMBARD" in line:
                        self.isLombardEnabled = eval(line.split("=")[-1])
                    elif "NOISE_RADIO_OFF" in line:
                        self.noise = eval(line.split("=")[-1])
                    elif "NOISE_RADIO_ON" in line:
                        self.noise_radio = eval(line.split("=")[-1])
                    elif "LAST" in line:
                        self.wPath = str(line.split("=")[-1]).replace("\n", "")
                if os.path.exists(self.wPath):
                    print("Working directory: %s" % self.wPath)
                else:
                    raise CorruptedTestError("Test directory not found")
        except FileNotFoundError:
            self.isFirstStart = True
            raise FileNotFoundError("Settings file not found!")
        return

    def _check_completed(self):
        lengths = []
        for i in list(self.results.keys()):
            lengths.append(len(self.results[i]))
        if len(self.results) == len(self.database[self.lang]):
            self.completed = min(lengths)
            if min(lengths) == max(lengths):
                self.status = False
        return self.status, self.completed

    # playback functions
    def play_command(self, cid):
        """
        Plays the command based on the current test language and on the command ID.
        The gain is adjusted based on the mouth calibration (if made) and on the Lombard Effect (if a recording of the
        background noise has been performed).
        """
        filename = self.phrasesPath + "/" + self.lang + "_" + str(cid) + ".wav"
        fs, data = read(filename)
        if self.isMouthCalibrated:
            while True:
                # wake word is pronounced with radio on
                if self.isLombardEnabled:
                    if int(cid) == 0 or int(cid) == 999:
                        total_gain = lombard(self.noise_radio) + self.gain
                    else:
                        total_gain = lombard(self.noise) + self.gain
                else:
                    total_gain = self.gain
                print("Adjusting gain (%0.2fdB)" % total_gain)
                try:
                    data = add_gain(data, total_gain)
                    break
                except SaturationError:
                    a = input(
                        "Cannot increase the volume of the wave file. Do you want to increase the amplifier volume "
                        "and redo the mouth calibration? (y/n to keep the max gain value possible).\n-->")
                    if str(a) == "y":
                        self.calibrate_mouth()
                    else:
                        break
        print("Playing %s" % filename)
        play_thread = Thread(target=play_data, args=(data, fs))
        play_thread.start()
        # play_data(data, fs)
        return

    def activate_mic(self, mode=1):
        """
        Function to activate the vehicle's microphone for the voice recognition.
        Modes:
        1 - Manual
        2 - Reproduce wake word (to be chosen among the audio files)
        3 - Send PTT can message
        """
        if mode == 1:
            input("Press PTT")
        elif mode == 2:
            try:
                print_square("Hey Maserati!", centering="center")
                self.play_command("000")
            except FileNotFoundError:
                print("Mode not implemented. Falling back to 1")
                pass
        else:
            input("Mode not implemented. Falling back to 1")
        return

    def cancel(self, mode=1):
        """
        Function to cancel recognition prompt

        1 - Reproduce "cancel" command
        2 - Send PTT can message
        """
        if mode == 1:
            try:
                print_square("Cancel", centering="center")
                self.play_command("999")
            except FileNotFoundError:
                input("'Cancel' command not found. Please place it under the command id '999'.")
                pass
        else:
            input("Mode not implemented. Falling back to 1")
        return

    # calibration functions
    def _make_calibration_file(self, duration=30):
        """
        Randomly chooses several audio files from the phrases folder and join them until a unique file of a fixed
        duration is made. The file is suitable for the calibration of the artificial mouth.
        """
        treshold = 100
        files = []
        for i in os.listdir(self.phrasesPath):
            if i.split(".")[-1] == "wav":
                files.append(self.phrasesPath + "/" + i)
        pdata = np.array([])
        while True:
            file = files[random.randint(1, len(files))]
            fs, calib_data = read(file)
            # cut silence at the beginning and at the end
            for _ in range(len(calib_data)):
                if abs(calib_data[1]) > treshold and abs(calib_data[-1]) > treshold:
                    break
                else:
                    if abs(calib_data[1]) < treshold:
                        calib_data = calib_data[1:]
                    if abs(calib_data[-1]) < treshold:
                        calib_data = calib_data[:-1]
            calib_data = np.concatenate((pdata, calib_data))
            # if the obtained file is longer than 30s, break the loop
            length = len(calib_data) / fs
            if length > duration:
                break
            pdata = calib_data
        len(calib_data)
        write(self.phrasesPath + "/calibration.wav", fs, calib_data.astype(np.int16))
        return fs, calib_data.astype(np.int16)

    def calibrate_mic(self):
        """
        Calibrates the microphone so that it expresses values in dBSPL.
        For that a 94dBSPL calibrator is mandatory.
        """
        self.recorder.calibrate(self.micChannel)
        self.recorder.save("%smic_calibration.wav" % self.settingsDir)
        self.recorder.save("%s/mic_calibration.wav" % self.wPath)
        self.save_settings()
        return

    def calibrate_ear(self):
        """
        Calibrates Oscar's ear so that it expresses values in dBSPL.
        For that a 94dBSPL calibrator is mandatory.
        """
        self.recorder.calibrate(channel=self.earChannel, reference=92.1)
        self.recorder.save("%sear_calibration.wav" % self.settingsDir)
        self.recorder.save("%s/ear_calibration.wav" % self.wPath)
        self.save_settings()
        return

    def calibrate_mouth(self, reference=94, max_attempts=6):
        """
        Reproduces a calibration file from the mouth, records it, measures its RMS power and, if needed, adjusts the
        gain and records again the calibration file.

        This operation is repeated until the RMS power is as close as possible to the nominal value of 94dBSPL.
        The number of maximum attempts can be decided and specified among the function's arguments.
        After the last attempt the last gain value is kept, whatever the difference between the RMS level and the
        nominal one is.
        """
        attempt = 1
        try:
            if self.recorder.calibrated:  # microphone has to be calibrated first
                print("Opening calibration file... ")
                try:
                    c_fs, c_data = read(self.phrasesPath + "/calibration.wav")
                except FileNotFoundError:
                    print("Calibration file not found! Creating a new one...", end='')
                    c_fs, c_data = self._make_calibration_file()
                print("done!")
                c_data_gain = add_gain(c_data, self.gain)
                recorded = self.recorder.play_and_record(c_data_gain, c_fs)[:, self.micChannel]
                recorded_dbspl = get_rms(recorded) + self.recorder.correction[self.micChannel]
                delta = reference - recorded_dbspl
                print_square("Target      = %0.2fdBSPL\n"
                             "Mouth RMS   = %0.2fdBSPL\n"
                             "delta       = %0.2fdB" % (reference, recorded_dbspl, -delta),
                             title="ATTEMPT %d of %d" % (attempt, max_attempts))
                while abs(delta) > 0.5:
                    attempt += 1
                    # add gain and record again until the intensity is close to 94dBSPL
                    self.gain = self.gain + delta
                    try:
                        print("\nApplying gain: %0.2fdB" % self.gain)
                        c_data_gain = add_gain(c_data, self.gain)
                        recorded = self.recorder.play_and_record(c_data_gain, c_fs)[:, self.micChannel]
                        recorded_dbspl = get_rms(recorded) + self.recorder.correction[self.micChannel]
                        delta = reference - recorded_dbspl
                        print_square("Target      = %0.2fdBSPL\n"
                                     "Mouth RMS   = %0.2fdBSPL\n"
                                     "delta       = %0.2fdB" % (reference, recorded_dbspl, -delta),
                                     title="ATTEMPT %d of %d" % (attempt, max_attempts))
                    except SaturationError:
                        input("Cannot automatically increase the volume. Please manually increase the volume from "
                              "the amplifier knob and press ENTER to continue\n-->")
                        self.gain = self.gain - delta
                        self.calibrate_mouth()
                        return
                    if attempt == max_attempts:
                        break
                print("Calibration completed: %0.2fdB added" % self.gain)
                self.recorder.data = self.recorder.data[:, self.micChannel]
                self.recorder.save("%smouth_calibration.wav" % self.settingsDir)
                self.recorder.save("%s/mouth_calibration.wav" % self.wPath)
                self.isMouthCalibrated = True
                self.save_settings()
        except KeyboardInterrupt:
            print("Mouth calibration interrupted. Gain value: %0.2f" % self.gain)
            self.isMouthCalibrated = True
            self.save_settings()
        return self.gain

    # Measure noise level
    def measure_noise(self, seconds=5):
        noise = self.recorder.record(seconds)[:, 1]
        noise_w = a_weight(noise, self.recorder.fs).astype(np.int16)
        self.noise = get_rms(noise_w) + self.recorder.correction[1]
        print_square("Noise intensity: %0.2fdBA\nLombard effect: %0.2fdB"
                     % (self.noise, lombard(self.noise)), title="RADIO OFF")
        self.recorder.save("%s/noise_radio_off.wav" % self.wPath)
        self.isSaved = False
        return self.noise

    def measure_noise_radio(self, seconds=5):
        noise = self.recorder.record(seconds)[:, 1]
        noise_w = a_weight(noise, self.recorder.fs).astype(np.int16)
        self.noise_radio = get_rms(noise_w) + self.recorder.correction[1]
        print_square("Noise intensity: %0.2fdBA\nLombard effect: %0.2fdB"
                     % (self.noise_radio, lombard(self.noise_radio)), title="RADIO ON")
        self.recorder.save("%s/noise_radio_on.wav" % self.wPath)
        self.isSaved = False
        return self.noise_radio

    def listen_noise(self, seconds=5):
        # Only background noise
        input("\nMeasuring background noise with radio OFF. Press ENTER to continue.\n-->")
        self.measure_noise(seconds)
        # Background noise and radio on
        input("\nMeasuring background noise with radio ON. Press ENTER to continue.\n-->")
        self.measure_noise_radio(seconds)
        return self.noise, self.noise_radio

    def execution(self, translate=False):
        """
        Execute the whole test routine for the chosen language.

        If the test has already started, resume it.
        """
        clear_console()
        # Test begins
        preconditions = []
        expected = []
        if not self.status:
            # start test from 0
            print_square("Beginning test... Press ENTER when you are ready")
            input("-->")
            self.log("MAY THE FORCE BE WITH YOU", self.logname)  # the first line of the log file
            self.results = {}
            self.status = True
        else:
            # resume the test
            print_square("Resuming test from %d... Press ENTER when you are ready" % (self.current_test + 1))
            input("-->")
            self.log("WELCOME BACK", self.logname)

        # takes just the commands for the chosen language
        test = self.database[self.lang]
        try:  # if available, imports the array for the preconditions and expected behaviour
            preconditions = self.database["preconditions"]
            expected = self.database["expected"]
        except KeyError:
            pass
        self.log("SELECTED LANGUAGE: %s - %s" % (self.lang, langDict[self.lang]), self.logname)
        if self.recorder.calibrated[self.earChannel]:
            self.listen_noise()
            input("Press ENTER to continue\n-->")
        i = 0
        try:
            for i in range(self.current_test, len(self.testlist)):
                clear_console()
                print_square("%s: TEST %d OUT OF %d" % (langDict[self.lang], i + 1, len(self.testlist)))
                try:
                    input("Preconditions:\n%s\n\nPress ENTER\n-->"
                          % (preconditions[self.testlist[i]].replace("\n", "")))
                except NameError:
                    pass
                except IndexError:
                    print("No preconditions for NLU commands!")
                self.log("=========================== TEST #%03d ==========================="
                    % (self.testlist[i] + 1), self.logname)
                while True:
                    for test_index in range(len(test[self.testlist[i]])):
                        cid = test[self.testlist[i]][test_index].split("\t")[
                            0]  # reading database, splits commands into command id and phrase
                        command = test[self.testlist[i]][test_index].split("\t")[1].replace("\n", "")
                        try:
                            next_command = test[self.testlist[i]][test_index + 1].split("\t")[1].replace("\n", "")
                        except IndexError:
                            next_command = "End"
                        try:
                            exp = expected[self.testlist[i]][test_index].replace("\n", "")
                        except IndexError:
                            exp = "None"
                        if cid == "000":
                            attempt = 0
                            max_attempts = 8
                            while True:
                                # activate the infotainment microphone for the voice recognition
                                # (1: manual, 2: wake word, 3: automatic)
                                self.activate_mic(self.mic_mode)
                                if self.mic_mode == 2:
                                    attempt += 1
                                    if attempt == max_attempts:
                                        print("\nWake word not recognized for %d times. Manually activate the MIC and"
                                              "press ENTER to continue...\n-->" % max_attempts)
                                        self.log("WAKE WORD NOT RECOGNIZED. SWITCHING TO MANUAL MODE", self.logname)
                                        break
                                    self.log("HEY MASERATI", self.logname)
                                    self.issued_ww += 1
                                print("Press ENTER to continue ('r' to repeat)\n-->", end="")
                                if getch().decode("utf-8") == 'r':
                                    print("\nRepeating...")
                                    self.log("REPEATING WAKEWORD", self.logname)
                                else:
                                    self.log("MIC_ACTIVATED", self.logname)
                                    self.recognized_ww += 1
                                    break
                        else:
                            try:
                                while True:
                                    print("\nReproducing %s_%s.wav - '%s'" % (self.lang, cid, command))
                                    try:
                                        # the mouth reproduces the command (after adjusting the gain, if wanted)
                                        self.play_command(cid)
                                    except Exception as e:
                                        print("ERROR: %s" % e)
                                    self.log("OSCAR: <<%s>> (%s_%s.wav)" % (command, self.lang, cid), self.logname)
                                    try:
                                        print("Expected behaviour --> %s\n" % exp)
                                    except NameError:
                                        pass
                                    # PLACE HERE THE FUNCTION TO LISTEN TO THE RADIO RESPONSE
                                    response = "[Answer]"
                                    if translate:
                                        translation = "Translation"
                                        self.log("RADIO: <<%s>> - <<%s>>" % (response, translation), self.logname)
                                    else:
                                        self.log("RADIO: <<%s>>" % response, self.logname)
                                    if len(test[self.testlist[i]]) > 1:
                                        print("Press ENTER to proceed with next step (%s) or 'r' to repeat\n-->"
                                              % next_command)
                                        q = getch()
                                        if q.decode("utf-8") == "r":
                                            print("\n\nRepeating step...", end="")
                                            self.log("REPEATING STEP", self.logname)
                                        else:
                                            break
                                    else:
                                        break
                            except KeyboardInterrupt:
                                self.log("CANCEL", self.logname)
                                break
                    self.cancel(1)
                    result = str(input("\nResult: 1(passed), 0(failed), r(repeat all)\n-->"))
                    r_time = now()
                    print(result)
                    self.current_test += 1  # status updated
                    if result != "r":
                        while True:
                            if result == "0":
                                self.log("END_TEST #%03d: FAILED" % (i + 1), self.logname)
                                note = input("Write notes if needed: ")
                                if len(note) > 0:
                                    self.log("NOTE #%03d: %s" % ((i + 1), note), self.logname)
                                result = "%s\t%s\t%s\t" % (result, note, r_time.replace("_", " "))
                                self.failed.append(i + 1)
                                input("(ENTER)-->")
                                break
                            elif result == "1":
                                self.log("END_TEST #%03d: PASSED" % (i + 1), self.logname)
                                self.passes += 1
                                note = input("Write notes if needed: ")
                                if len(note) > 0:
                                    self.log("NOTE #%03d: %s" % ((i + 1), note), self.logname)
                                result = "%s\t%s\t%s\t" % (result, note, r_time.replace("_", " "))
                                break
                            else:
                                # TODO: fix bug when answered "r"
                                result = str(input("INVALID INPUT: 1(passed), 0(failed), r(repeat all)\n-->"))
                        break
                    else:  # repeats test
                        self.log("REPEATING", self.logname)
                    # cancels prompt
                    input("Press ENTER -->")
                try:
                    # at the end of the selected test, writes the results into a array
                    self.results[str(self.testlist[i] + 1)].append(result)
                except KeyError:
                    self.results[str(self.testlist[i] + 1)] = []
                    self.results[str(self.testlist[i] + 1)].append(result)
                self.save()
                self.status, self.completed = self._check_completed()
                if self.completed > 0 and not self.status:
                    self._complete()
        except KeyboardInterrupt:
            print("------------------------------------------------------------------")
            print("Test aborted! Saving...")
            self.log("TEST_INTERRUPTED", self.logname)
            self.current_test = self.testlist[i]
            self.log("TEST_STATUS: %03d" % self.current_test, self.logname)
            self.save()  # save current progress of the test
            return

        except Exception as e:
            print("------------------------------------------------------------------")
            print("Test aborted due to a error (%s)! Saving..." % e)
            self.log("ERROR %s" % e, self.logname)
            self.current_test = self.testlist[i]
            self.log("TEST_STATUS: %03d" % self.current_test, self.logname)
            self.save()  # save current progress of the test
            return

        self._complete()
        self.save_conf()  # save current progress of the test
        clr_tmp()
        return self.current_test

    def _complete(self):
        self.log("======================================================", self.logname)
        self.log("TEST_STATUS: COMPLETED! CONGRATULATIONS", self.logname)
        self.log("======================================================", self.logname)
        self.status, self.completed = self._check_completed()
        self.current_test = 0
        self.save()  # save current progress of the test
        print_square("Test completed!\n\nSaving report as csv file")
        input('-->')
        self.print_report()
        return

    def print_report(self, filename = None):
        """
        Print the results in a csv file suitable for the analysis with Excel.
        """
        if filename is None:
            self.report_file = "%s/%s_report.csv" % (self.wPath, self.testName)
        else:
            self.report_file = filename
        # sort results
        self.results = sort_dict(self.results)
        while True:
            try:
                print("\nSaving test results into %s...\n" % self.report_file)
                with open(self.report_file, "w", encoding="utf-16") as r:
                    r.write("LANGUAGE: %s\n" % self.lang)
                    r.write("WW RATIO:\t %0.5f\n" % (self.recognized_ww / self.issued_ww))
                    r.write("TEST N.\tRESULT\tCOMMENT\tTIMESTAMP\n")
                    for i in range(227):
                    # for i in range(len(self.testlist)):
                        # write key
                        if str(i+1) in list(self.results.keys()):
                            print("Writing %s" % (i+1))
                            r.write("%s\t" % (i+1))
                            for result in self.results[str(i+1)]:
                                r.write("%s" % result)
                        else:
                            print("Creating %s" % (i+1))
                            r.write("%s\tNT" % (i+1))
                        r.write("\n")

                self.log("PRINTED REPORT", self.logname)
                break
            except PermissionError:
                input("Can't access to file! Make sure it's not open and press ENTER to continue\n-->")
        return


if __name__ == "__main__":
    # show splash screen
    splash()
    # declare a new test
    t = Test()
    # execute test
    t.execution()
