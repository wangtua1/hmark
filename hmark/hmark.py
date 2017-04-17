#! /usr/bin/env python2
"""
Version 3.0~ of Hashmarker (CSSA)
Author: Seulbae Kim (seulbae@korea.ac.kr)
http://github.com/squizz617/discovuler-advanced/hmark
"""

import Tkinter
import tkFileDialog
import ttk

import urllib2
import platform
import sys
import os
import time
from re import compile, findall
import webbrowser
from hashlib import md5

import multiprocessing
import subprocess

import parseutility
import version
import get_cpu_count

import argparse

""" GLOBALS """
localVersion = version.version
osName = ""
urlBase = "http://iotcube.korea.ac.kr/"
urlCheck = urlBase + "getbinaryversion/wf1/"
urlDownload = urlBase + "downloads"


def get_platform():
    global osName

    pf = platform.platform()
    if "Windows" in pf:
        osName = "win"
    elif "Linux" in pf:
        osName = "linux"
    else:
        osName = "osx"


def check_update():
    global localVersion

    if len(localVersion.split('.')) < 3:
        localVersion += ".0"
    print "Local version: " + localVersion

    try:
        response = urllib2.urlopen(urlCheck + osName[0])
    except Exception:
        print "[-] Update server is not responding."
        print "    Please check your network connection or firewall and try again."
        print "    To bypass update checking, run with [--no-update-check] option."
        raw_input("Press Enter to continue...")
        sys.exit()

    latestVersion = "0.0.0"  # for exception handling

    html = response.read()
    latestVersion = html

    if len(latestVersion.split('.')) < 3:
        latestVersion += '.0'

    print "Latest version: " + latestVersion,

    # compare version
    cvList = localVersion.split('.')
    c1 = int(cvList[0])
    c2 = int(cvList[1])
    c3 = int(cvList[2])
    lvList = latestVersion.split('.')
    l1 = int(lvList[0])
    l2 = int(lvList[1])
    l3 = int(lvList[2])

    updateFlag = 0

    if localVersion == latestVersion:
        updateFlag = 0
    elif c1 < l1:
        updateFlag = 1
    elif c1 == l1:
        if c2 < l2:
            updateFlag = 1
        elif c2 == l2:
            if c3 < l3:
                updateFlag = 1
            else:
                updateFlag = 0
        else:
            updateFlag = 0
    else:
        updateFlag = 0

    if updateFlag:
        print "(out-of-date)"
        print "[-] Your Hasher is not up-to-date."
        print "    Please download and run the latest version."
        print "    Proceeding to the download page."
        print "    To bypass update checking, run with [--no-update-check] option."

        webbrowser.open(urlDownload)
        raw_input("Press Enter to continue...")
        sys.exit()
    else:
        print "(up-to-date)"


def parseFile_shallow_multi(f):
    functionInstanceList = parseutility.parseFile_shallow(f, "GUI")
    return (f, functionInstanceList)


def parseFile_deep_multi(f):
    functionInstanceList = parseutility.parseFile_deep(f, "GUI")
    return (f, functionInstanceList)


class App:
    def __init__(self, master):
        self.master = master
        self.defaultbg = master.cget('bg')

        self.mainWidth = 900  # width for the Tk root (root == master of this class)
        if osName == "osx":
            self.mainHeight = 700  # height for the Tk root
        else:
            self.mainHeight = 650

        self.screenWidth = master.winfo_screenwidth()  # width of the screen
        self.screenHeight = master.winfo_screenheight()  # height of the screen

        self.x = (self.screenWidth / 2) - (self.mainWidth / 2)
        self.y = (self.screenHeight / 2) - (self.mainHeight / 2)

        master.geometry("%dx%d+%d+%d" % (self.mainWidth, self.mainHeight, self.x, self.y))
        master.resizable(width=False, height=False)

        """ MENU """
        self.menubar = Tkinter.Menu(master, tearoff=1)
        self.menubar.add_command(label="HELP", command=self.show_help)
        self.menubar.add_command(label="ABOUT", command=self.show_about)
        master.config(menu=self.menubar)

        """ BROWSE DIRECTORY """
        frmDirectory = Tkinter.Frame(master)
        frmDirectory.pack(fill=Tkinter.BOTH, padx=50, pady=(20, 0))

        self.directory = Tkinter.StringVar()
        self.directory.set('Choose the root directory of your program.')
        self.btnDirectory = Tkinter.Button(frmDirectory, text="Browse directory", command=self.askDirectory)
        self.btnDirectory.pack(side=Tkinter.LEFT)

        self.lblSelected = Tkinter.Label(frmDirectory, fg=self.defaultbg, text="Selected: ")
        self.lblSelected.pack(side=Tkinter.LEFT, padx=(10, 0))
        self.lblDirectory = Tkinter.Label(frmDirectory, fg="Red", textvariable=self.directory)
        self.lblDirectory.pack(side=Tkinter.LEFT)

        """ ABSTRACTION """
        frmAbstraction = Tkinter.Frame(master)
        frmAbstraction.pack(fill=Tkinter.BOTH)

        lblfrmAbstraction = Tkinter.LabelFrame(frmAbstraction, text="Select abstraction mode")
        lblfrmAbstraction.pack(fill=Tkinter.BOTH, expand="yes", padx=50, pady=10)

        self.absLevel = Tkinter.IntVar()
        R1 = Tkinter.Radiobutton(
            lblfrmAbstraction,
            text="Abstraction OFF: Detect exact clones only",
            variable=self.absLevel,
            value=0,
            command=self.selectAbst
        )
        R2 = Tkinter.Radiobutton(
            lblfrmAbstraction,
            text="Abstraction ON: Detect near-miss (similar) clones, as well as exact clones",
            variable=self.absLevel,
            value=4,
            command=self.selectAbst
        )
        R1.pack(side=Tkinter.LEFT, anchor=Tkinter.W)
        R2.pack(side=Tkinter.RIGHT, anchor=Tkinter.W)

        """ GENERATE """
        frmGenerate = Tkinter.Frame(master)
        frmGenerate.pack(fill=Tkinter.BOTH, padx=50, pady=5)
        self.btnGenerate = Tkinter.Button(
            frmGenerate,
            width=10000,
            text="----- Generate hashmark -----",
            state="disabled",
            # command=lambda:self.generate("GUI", "", "")
            command=self.generate
        )
        self.btnGenerate.pack(side=Tkinter.BOTTOM)

        """ PROCESS """
        frmProcess = Tkinter.Frame(master)
        frmProcess.pack(fill=Tkinter.X)

        scrollbar = Tkinter.Scrollbar(frmProcess)
        scrollbar.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
        self.listProcess = Tkinter.Listbox(frmProcess, state="disabled", width=600, height=26,
                                           yscrollcommand=scrollbar.set, selectmode=Tkinter.SINGLE)
        # self.listProcess.insert(END, "")
        self.listProcess.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH)
        scrollbar.config(command=self.listProcess.yview)

        """ PROGRESSBAR """
        frmPgbar = ttk.Frame(master)
        frmPgbar.pack(expand=True, fill=Tkinter.BOTH, side=Tkinter.TOP)

        self.progress = 0
        self.progressbar = ttk.Progressbar(
            frmPgbar,
            orient="horizontal",
            mode="determinate",
            value=self.progress,
            maximum=1
        )
        self.progressbar.pack(expand=True, fill=Tkinter.BOTH, side=Tkinter.TOP)

        """ QUIT """
        frmBottom = Tkinter.Frame(master)  # , bd=20)
        frmBottom.pack(fill=Tkinter.BOTH)

        self.btnOpenFolder = Tkinter.Button(
            frmBottom,
            width=15,
            text="Open hidx folder",
            state="disabled",
            command=self.openFolder
        )
        self.btnQuit = Tkinter.Button(
            frmBottom,
            width=15,
            text="QUIT",
            command=frmBottom.quit
        )
        self.btnOpenFolder.pack(side=Tkinter.LEFT, padx=50)
        self.btnQuit.pack(side=Tkinter.RIGHT, padx=50, pady=15)

    def openFolder(self):
        path = os.path.join(os.getcwd(), "hidx")
        if osName == "win":
            subprocess.Popen(
                ["explorer", "/select,", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        elif osName == "linux":
            subprocess.Popen(
                ["xdg-open", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        elif osName == "osx":  # needs testing
            subprocess.Popen(
                ["open", "-R", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def generate(self):
        directory = self.directory.get()
        absLevel = int(self.absLevel.get())
        self.progress = 0

        proj = directory.replace('\\', '/').split('/')[-1]
        timeIn = time.time()
        numFile = 0
        numFunc = 0
        numLine = 0

        projDic = {}
        hashFileMap = {}

        self.listProcess.config(state="normal")
        self.listProcess.insert(Tkinter.END, "Loading source files... This may take a few minutes.")
        self.listProcess.update()

        fileList = parseutility.loadSource(directory)
        numFile = len(fileList)

        if numFile == 0:
            self.listProcess.insert(Tkinter.END,
                                    "Error: Failed loading source files. Check if you selected proper directory, or if your project contains .c or .cpp files.")
        else:
            # self.listProcess.insert(END, "")
            self.listProcess.insert(Tkinter.END, "Load complete. Generating hashmark...")
            # self.listProcess.insert(END, "")
            # self.listProcess.insert(END, "")

            if absLevel == 0:
                func = parseFile_shallow_multi
            else:
                func = parseFile_deep_multi

            cpu_count = get_cpu_count.get_cpu_count()
            if cpu_count != 1:
                cpu_count -= 1

            pool = multiprocessing.Pool(processes=cpu_count)
            for idx, tup in enumerate(pool.imap_unordered(func, fileList)):
                f = tup[0]
                functionInstanceList = tup[1]

                fullName = proj + f.split(proj, 1)[1]
                pathOnly = f.split(proj, 1)[1][1:]
                progress = (float)(idx + 1) / numFile

                self.progressbar["value"] = progress
                self.progressbar.update()
                a = self.listProcess.insert(Tkinter.END, "[+] " + f)
                self.listProcess.see("end")

                numFunc += len(functionInstanceList)

                if len(functionInstanceList) > 0:
                    numLine += functionInstanceList[0].parentNumLoc

                for f in functionInstanceList:
                    f.removeListDup()
                    path = f.parentFile
                    absBody = parseutility.abstract(f, absLevel)[1]
                    absBody = parseutility.normalize(absBody)
                    funcLen = len(absBody)

                    if funcLen > 50:
                        hashValue = md5(absBody).hexdigest()

                        try:
                            projDic[funcLen].append(hashValue)
                        except KeyError:
                            projDic[funcLen] = [hashValue]
                        try:
                            hashFileMap[hashValue].extend([pathOnly, f.funcId])
                        except KeyError:
                            hashFileMap[hashValue] = [pathOnly, f.funcId]
                    else:
                        numFunc -= 1  # decrement numFunc by 1 if funclen is under threshold

            self.listProcess.insert(Tkinter.END, "")
            self.listProcess.insert(Tkinter.END, "Hash index successfully generated.")
            self.listProcess.see("end")
            self.listProcess.insert(Tkinter.END, "")
            self.listProcess.see("end")
            self.listProcess.insert(Tkinter.END, "Saving hash index to file...")
            self.listProcess.see("end")

            try:
                os.mkdir("hidx")
            except:
                pass
            packageInfo = str(localVersion) + ' ' + str(proj) + ' ' + str(numFile) + ' ' + str(numFunc) + ' ' + str(
                numLine) + '\n'
            with open("hidx/hashmark_" + str(absLevel) + "_" + proj + ".hidx", 'w') as fp:
                fp.write(packageInfo)

                for key in sorted(projDic):
                    fp.write(str(key) + '\t')
                    for h in list(set(projDic[key])):
                        fp.write(h + '\t')
                    fp.write('\n')

                fp.write('\n=====\n')

                for key in sorted(hashFileMap):
                    fp.write(str(key) + '\t')
                    for f in hashFileMap[key]:
                        fp.write(str(f) + '\t')
                    fp.write('\n')

            timeOut = time.time()

            self.listProcess.insert(Tkinter.END, "Done.")
            self.listProcess.see("end")
            self.listProcess.insert(Tkinter.END, "")
            self.listProcess.insert(Tkinter.END, "Elapsed time: %.02f sec." % (timeOut - timeIn))
            self.listProcess.see("end")

            self.listProcess.insert(Tkinter.END, "Program statistics:")
            self.listProcess.insert(Tkinter.END, " - " + str(numFile) + ' files;')
            self.listProcess.insert(Tkinter.END, " - " + str(numFunc) + ' functions;')
            self.listProcess.insert(Tkinter.END, " - " + str(numLine) + ' lines of code.')
            self.listProcess.see("end")

            self.listProcess.insert(Tkinter.END, "")
            self.listProcess.insert(Tkinter.END,
                                    "Hash index saved to: " + os.getcwd().replace("\\", "/") + "/hidx/hashmark_" + str(
                                        absLevel) + "_" + proj + ".hidx")
            self.listProcess.see("end")
            self.btnOpenFolder.config(state="normal")

    def selectAbst(self):
        selection = str(self.absLevel.get())

    def askDirectory(self):
        selectedDirectory = tkFileDialog.askdirectory()
        if len(selectedDirectory) > 1:
            self.lblSelected.config(fg="Black")
            self.lblDirectory.config(fg="Black")
            self.directory.set(selectedDirectory)
            self.btnGenerate.config(state="normal")

    def show_about(self):
        top = Tkinter.Toplevel(padx=20, pady=10)
        if osName == "win":  # this only works for windows.
            top.withdraw()  # temporarily hide widget for better UI
        aboutMessage = """
HMark is an hash index generator for vulnerable code clone detection.

Developed by CSSA.
http://iotcube.net
"""
        msg = Tkinter.Message(top, text=aboutMessage)
        msg.pack()
        btnOkay = Tkinter.Button(top, text="Okay", command=top.destroy)
        btnOkay.pack()

        top.update()
        # self.master.update_idletasks()
        topw = top.winfo_reqwidth()  # width of this widget
        toph = top.winfo_reqheight()  # height of this widget
        parentGeo = self.master.geometry().split('+')
        parentX = int(parentGeo[1])  # X coordinate of parent (the main window)
        parentY = int(parentGeo[2])  # Y coordinate of parent

        top.geometry("+%d+%d" % (parentX + self.mainWidth / 2 - topw / 2, parentY + self.mainHeight / 2 - toph / 2))
        top.resizable(width=False, height=False)
        top.grab_set_global()
        top.title("About HMark...")
        if osName == "win":
            top.deiconify()  # show widget, as its position is set

    def show_help(self):
        top = Tkinter.Toplevel(padx=20, pady=10)
        if osName == "win":  # this only works for windows.
            top.withdraw()  # temporarily hide widget

        helpMessage = """
1. Select the root directory of your package under which source code is located.\n
2. Choose the abstraction mode.
- OFF: HMARK will detect only exact clones.
- ON: HMARK will detect near-miss clones along with exact clones, by tolerating changes in parameter, variable names, types, and called functions.\n
3. Generate Hashmark.
		"""
        msg = Tkinter.Message(top, text=helpMessage)
        btnOkay = Tkinter.Button(top, text="Okay", command=top.destroy)
        self.master.update_idletasks()

        msg.pack()
        btnOkay.pack()

        top.update()
        topw = top.winfo_reqwidth()  # width of this widget
        toph = top.winfo_reqheight()  # height of this widget

        parentGeo = self.master.geometry().split('+')
        parentX = int(parentGeo[1])  # width of parent (the main window)
        parentY = int(parentGeo[2])  # height of parent

        top.geometry("+%d+%d" % (parentX + self.mainWidth / 2 - topw / 2, parentY + self.mainHeight / 2 - toph / 2))
        top.resizable(width=False, height=False)
        top.grab_set_global()
        top.title("Help")
        if osName == "win":
            top.deiconify()  # show widget, as its position is set


def run_gui():
    global localVersion
    global icon
    root = Tkinter.Tk()
    app = App(root)
    root.title("HMark ver " + str(localVersion))

    try:  # if icon is available
        icon = resource_path("icon.gif")
        img = Tkinter.PhotoImage(file=icon)
        root.tk.call('wm', 'iconphoto', root._w, img)
    except Tkinter.TclError:  # if, for some reason, icon isn't available
        pass

    root.mainloop()

    try:
        root.destroy()
        print "Farewell!"
    except Tkinter.TclError:
        print "GUI process terminated."


def generate_cli(targetPath, isAbstraction):
    directory = targetPath.rstrip('/')

    if isAbstraction.lower() == "on":
        absLevel = 4
    else:
        absLevel = 0

    proj = directory.replace('\\', '/').split('/')[-1]
    print "PROJ:", proj
    timeIn = time.time()
    numFile = 0
    numFunc = 0
    numLine = 0

    projDic = {}
    hashFileMap = {}

    print "[+] Loading source files... This may take a few minutes."

    fileList = parseutility.loadSource(directory)
    numFile = len(fileList)

    if numFile == 0:
        print "[-] Error: Failed loading source files."
        print "    Check if you selected proper directory, or if your project contains .c or .cpp files."
        sys.exit()
    else:
        print "[+] Load complete. Generating hashmark..."

        if absLevel == 0:
            func = parseFile_shallow_multi
        else:
            func = parseFile_deep_multi

        cpu_count = get_cpu_count.get_cpu_count()
        if cpu_count != 1:
            cpu_count -= 1

        pool = multiprocessing.Pool(processes=cpu_count)
        for idx, tup in enumerate(pool.imap_unordered(func, fileList)):
            f = tup[0]
            functionInstanceList = tup[1]

            fullName = proj + f.split(proj, 1)[1]
            pathOnly = f.split(proj, 1)[1][1:]
            progress = (float)(idx + 1) / numFile

            try:
                # http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
                rows, columns = subprocess.check_output(['stty', 'size']).split()
            except ValueError:
                columns = 80

            progress = 100 * (float)(idx + 1) / numFile
            buf = "\r%.2f%% %s" % (progress, fullName)
            buf += " " * (int(columns) - len(buf))
            sys.stdout.write(buf)
            sys.stdout.flush()

            numFunc += len(functionInstanceList)

            if len(functionInstanceList) > 0:
                numLine += functionInstanceList[0].parentNumLoc

            for f in functionInstanceList:
                f.removeListDup()
                path = f.parentFile
                absBody = parseutility.abstract(f, absLevel)[1]
                absBody = parseutility.normalize(absBody)
                funcLen = len(absBody)

                if funcLen > 50:
                    hashValue = md5(absBody).hexdigest()

                    try:
                        projDic[funcLen].append(hashValue)
                    except KeyError:
                        projDic[funcLen] = [hashValue]
                    try:
                        hashFileMap[hashValue].extend([pathOnly, f.funcId])
                    except KeyError:
                        hashFileMap[hashValue] = [pathOnly, f.funcId]
                else:
                    numFunc -= 1  # decrement numFunc by 1 if funclen is under threshold

        print ""
        print "[+] Hash index successfully generated."
        print "[+] Saving hash index to file...",

        packageInfo = str(localVersion) + ' ' + str(proj) + ' ' + str(numFile) + ' ' + str(numFunc) + ' ' + str(
            numLine) + '\n'
        with open("hidx/hashmark_" + str(absLevel) + "_" + proj + ".hidx", 'w') as fp:
            fp.write(packageInfo)

            for key in sorted(projDic):
                fp.write(str(key) + '\t')
                for h in list(set(projDic[key])):
                    fp.write(h + '\t')
                fp.write('\n')

            fp.write('\n=====\n')

            for key in sorted(hashFileMap):
                fp.write(str(key) + '\t')
                for f in hashFileMap[key]:
                    fp.write(str(f) + '\t')
                fp.write('\n')

        timeOut = time.time()

        print "(Done)"
        print ""
        print "[+] Elapsed time: %.02f sec." % (timeOut - timeIn)
        print "Program statistics:"
        print " - " + str(numFile) + ' files;'
        print " - " + str(numFunc) + ' functions;'
        print " - " + str(numLine) + ' lines of code.'
        print ""
        print "[+] Hash index saved to: " + os.getcwd().replace("\\", "/") + "/hidx/hashmark_" + str(
            absLevel) + "_" + proj + ".hidx"


def run_cli(targetPath, isAbstraction):
    generate_cli(targetPath, isAbstraction)
    print "Farewell!"


def main():
    try:
        os.mkdir("hidx")
    except:
        pass

    get_platform()

    progStr = "hmark_" + localVersion + "_" + osName
    if osName == "win":
        progStr += ".exe"

    ap = argparse.ArgumentParser(
        prog=progStr
    )

    ap.add_argument(
        "-c",
        "--cli-mode",
        dest="cli_mode",
        nargs=2,
        metavar=("path", "ON/OFF"),
        required=False,
        help="run hmark without GUI by specifying the path to the target directory, and the abstraction mode"
    )

    ap.add_argument(
        "-n",
        "--no-updatecheck",
        dest="no_update_check",
        action="store_true",
        required=False,
        help="bypass update checking (not recommended)"
    )
    ap.add_argument(
        "-V",
        "--version",
        dest="version",
        action="store_true",
        required=False,
        help="print hmark version and exit"
    )
    args = ap.parse_args()

    if args.version:
        print "hmark " + localVersion + " for " + osName
        sys.exit()

    if args.no_update_check:
        print "Bypassed the update checker."
    else:
        check_update()

    if osName == "linux" or osName == "osx":
        try:
            msg = subprocess.check_output("java -version", stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            print "Java error:", e
            print "Please try again after installing JDK."
            sys.exit()

    if args.cli_mode:
        if os.path.isdir(args.cli_mode[0]) is False:
            print "[-] Directory does not exist:", args.cli_mode[0]
            print "    Please specify the right directory to your target."
            sys.exit()

        if args.cli_mode[1].isalpha():
            if args.cli_mode[1].lower() == "on" or args.cli_mode[1].lower() == "off":
                print "Running in CLI mode"
                print "TARGET: " + args.cli_mode[0]
                print "ABSTRACTION: " + args.cli_mode[1]
                run_cli(args.cli_mode[0], args.cli_mode[1])
            else:
                print "[-] Bad parameter: " + args.cli_mode[1]
                print "    Accepted parameters are ON or OFF."
                sys.exit()

    else:
        print "Running GUI"
        run_gui()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


try:
    # Python 3.4+
    if sys.platform.startswith("win"):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking

if sys.platform.startswith("win"):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')


    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen

""" EXECUTE """
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
