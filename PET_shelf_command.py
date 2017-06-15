import maya.cmds as cmds
import importlib, imp, os

def petFail(mode):
    print "\n"
    print "--------- PET Script Output ---------"
    if mode == 1:
        print "Could not find PET folder inside scripts dir."
    if mode == 2:
        print "PET folder in user script directory contains no python files."
    if mode == 3:
        print "Could not import script module."
    else:
        print "unknown error"
    return
    
def load_from_file(filepath):
    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
    try:
        moduleFile = imp.load_source(mod_name, filepath)
        return moduleFile
    except  ImportError:
        petFail(3)
        return

userScriptDir = cmds.internalVar(userScriptDir=True)
highestVersion = 000

if cmds.file(userScriptDir + "PET", query=True, exists=True):
    petScriptDir = userScriptDir + "PET/"
    pyFiles = cmds.getFileList(folder=petScriptDir, filespec='*.py')
    if not pyFiles:
        petFail(2)
    for pyFile in pyFiles:
        scriptVersionInfo = pyFile.rsplit(".py")[0]
        scriptVersionInfo = scriptVersionInfo.rsplit("_", 2)
        if scriptVersionInfo[0] == "pfhor_export_tool" and scriptVersionInfo[1] == "version":
           if scriptVersionInfo[2] > highestVersion:
               highestVersion = scriptVersionInfo[2]
    if highestVersion > 0:
        scriptFile = petScriptDir + "pfhor_export_tool_version_" + highestVersion + ".py"
        exportUImodule = load_from_file(scriptFile)
        if exportUImodule:
            exportUImodule.exportUI(petScriptDir)
else:
    petFail(1)
    

