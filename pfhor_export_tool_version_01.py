import maya.cmds as cmds
import maya.mel as mel

#this script 

#names specific to pfhor
#------------------------------------------------------------------------------------------
#these are the names of the topmost parent nodes of the branches that contain a roll bone
#as a (direct or indirect) descendent
pfhor_roll_joints = [
    "Master_Hip_CNTRL",
    "Shoulder_CNTRL"
]

joints_to_delete_after_baking = [
    "chest_spine_joint",
    "waist_spine_joint",
    "L_Shoulder",
    "R_Shoulder"
]

globalControlCurveName = "globalCntrl"
topRootJoints = []
rowColLayout = None
otherParentNodes = []
fixOptions = ['Leave as is', 'Move into hierarchy'] #index 0 should have the default string, index 1 as the repair option string
textLabelNames = []
labelNames = {}
parented = {} #keep track of what was parented, so we can unparent later. parented[child]=parent
mainWidths = (140, 140)
optionsMenuNames = []
mainLayout = None
minTime = 0
maxTime = 0
minTimeField = None
maxTimeField = None
defaultNamespaceName = "Pfhor_Skel_"
userCurrentNameSpace = "" #remember namespace user is in before running script so that the script can return to this namespace


def exportUI(petScriptDir):
    global rowColLayout, mainWidths, mainLayout, minTime, maxTime, minTimeField, maxTimeField, globalControlCurveName
    #TODO turn this into a modal window
    #if not checkForExportablePfhorSkeleton():
    #    return
    if cmds.window("exportWindow", exists=True):
        cmds.deleteUI("exportWindow")
    minTime = int(cmds.playbackOptions(query=True, minTime=True))
    maxTime = int(cmds.playbackOptions(query=True, maxTime=True))
    window = cmds.window("exportWindow", title="Pfhor Export Tool", w=300, h=300, mnb=False, mxb=False, sizeable=False)
    mainLayout = cmds.columnLayout(w=300, h=300)
    imagePath = petScriptDir + "pet_banner2.jpg"
    cmds.image(w=300, h=100, image=imagePath)
    cmds.separator(h=10, style="none")
    rowColLayout = cmds.rowColumnLayout(nc=2, columnWidth=[(1,mainWidths[0]), (2,mainWidths[1])], columnOffset=[(1,"right", 10), (2,"right",10)])
    cmds.text(label="Select Root Joint : ", w=mainWidths[0])
    cmds.optionMenu("skeletonSel", label="", changeCommand=updateControlSels, w=mainWidths[1])
    populateSkelSel()
    cmds.separator(h=10, style="none", parent=rowColLayout)
    cmds.separator(h=10, style="none", parent=rowColLayout)
    cmds.separator(h=10, style="none", parent=rowColLayout)
    cmds.separator(h=10, style="none", parent=rowColLayout)
    if cmds.ls(globalControlCurveName):
        hasGlobalControl = True
    else:
        hasGlobalControl = False
    cmds.checkBox(label='Global control', value=hasGlobalControl)
    cmds.optionMenu("worldOrientation", label="WorldSpace")
    upAxis = cmds.upAxis(q=True, axis=True)
    if upAxis == "z":
        cmds.menuItem(label="+Z up", parent="worldOrientation")
        cmds.menuItem(label="+Y up", parent="worldOrientation")
    else:
        cmds.menuItem(label="+Y up", parent="worldOrientation")
        cmds.menuItem(label="+Z up", parent="worldOrientation")
    cmds.separator(h=20, style="none", parent=rowColLayout)
    cmds.separator(h=20, style="none", parent=rowColLayout)
    cmds.text(label='Unparented Control Nodes :', parent=rowColLayout, w=300, font="boldLabelFont")
    cmds.text(label="", parent=rowColLayout)
    updateControlSels()
    cmds.separator(h=10, style="none", parent=rowColLayout)
    cmds.separator(h=10, style="none", parent=rowColLayout)
    cmds.text("Start Frame: ", parent=rowColLayout)
    minTimeField = cmds.textField("", text=str(minTime), parent=rowColLayout, changeCommand=minFrameNumChanged)
    cmds.text("End Frame: ", parent=rowColLayout)
    maxTimeField = cmds.textField(text=str(maxTime), parent=rowColLayout, changeCommand=maxFrameNumChanged)
    cmds.separator(h=20, style="none", parent=mainLayout)
    rowColLayout2 = cmds.rowColumnLayout(nc=1, columnWidth=[(1,300)], columnOffset=[(1, "both", 80)], parent=mainLayout)
    cmds.button("exportButton", label="Bake", w=140, h=30, command=exportFBX, parent=rowColLayout2)
    cmds.separator(h=20, style="none", parent=mainLayout)
    cmds.showWindow(window)


def minFrameNumChanged(*args):
    global minTimeField
    newNum = int(float(str(args[0])))
    cmds.textField(minTimeField, edit=True, text=newNum)


def maxFrameNumChanged(*args):
    global maxTimeField
    newNum = int(float(str(args[0])))
    cmds.textField(maxTimeField, edit=True, text=newNum)


def populateSkelSel():
    global topRootJoints
    joints =  cmds.ls(type="joint")
    for joint in joints:
        #joints which do not have parents who are also joints, eg a root joint
        relatives = cmds.listRelatives(joint, allParents=True, fullPath=True, type="joint")
        if not relatives:
            #we have topmost level joint
            topRootJoints.append(joint)
            cmds.menuItem(label = joint, parent="skeletonSel")


def getOtherParentNodes(itemSelected):
    global topRootJoints, otherParentNodes, globalControlCurveName
    nbcurves =  cmds.ls(type="nurbsCurve")
    parentNodes = []
    #find the topmost control curves (under the global control)
    if cmds.ls(globalControlCurveName):
        for nbcurve in nbcurves:
            newNode = ""
            relatives = cmds.listRelatives(nbcurve, allParents=True, fullPath=True)
            if len(relatives[0].split(r'|')) == 2:
                newNode = relatives[0].split(r'|')[1]
            elif len(relatives[0].split(r'|')) > 2:
                newNode = relatives[0].split(r'|')[2]
            if newNode:
                if newNode not in parentNodes:
                   parentNodes.append(newNode)
    else:
        for nbcurve in nbcurves:
            relatives = cmds.listRelatives(nbcurve, allParents=True, fullPath=True)
            newNode = relatives[0].split(r'|')[1]
            if newNode not in parentNodes:
                   parentNodes.append(newNode)
    #each time an item is selected from skeletonSel repopulate the control select forums with only those controls
    #that are not associated with the skeleton
    otherParentNodes = []
    for parentNode in parentNodes:
        relatives = cmds.listRelatives(parentNode, allDescendents=True, type="joint")
        if relatives and itemSelected not in relatives and not itemSelected == parentNode and parentNode not in otherParentNodes:
            otherParentNodes.append(parentNode)
    return otherParentNodes


def updateControlSels(*args):
    global otherParentNodes, topRootJoints, fixOptions, textLabelNames, labelNames, rowColLayout, mainWidths, optionsMenuNames, mainLayout
    if not args:
        itemSelected = topRootJoints[0]
    else:
        itemSelected = args[0]
    otherParentNodes = getOtherParentNodes(itemSelected)
    labelNames = {}
    if not textLabelNames:
        if otherParentNodes:
            for otherParentNode in otherParentNodes:
                cmds.separator(h=10, style="none", parent=rowColLayout)
                cmds.separator(h=10, style="none", parent=rowColLayout)
                name = "textLabel_" + str(len(textLabelNames))
                textLabelNames.append(name)
                name2 = "optionMenu_" + str(len(optionsMenuNames))
                optionsMenuNames.append(name2)
                aLabel = otherParentNode + "   "
                cmds.text(name, label=aLabel, parent=rowColLayout, w=mainWidths[0], align="right")
                lolz = cmds.optionMenu(name2, parent=rowColLayout, w=mainWidths[1])
                labelNames[name2] = otherParentNode
                for fixOption in fixOptions:
                    cmds.menuItem(name+"."+fixOption, label=fixOption, parent=lolz)
                if otherParentNode in pfhor_roll_joints:
                    cmds.optionMenu(name2, edit=True, select=2)
        else:
            cmds.separator(h=10, style="none", parent=rowColLayout)
            cmds.separator(h=10, style="none", parent=rowColLayout)
            cmds.text(label="No unparented control nodes for "+str(itemSelected), parent=rowColLayout, w=300)
            cmds.text(label="")
            cmds.separator(h=10, style="none", parent=rowColLayout)
            cmds.separator(h=10, style="none", parent=rowColLayout)
                
    else:
        for textLabel in textLabelNames:
            for otherParentNode in otherParentNodes:
                newLabel = otherParentNode + "   "
                cmds.text(textLabel, label=newLabel, edit=True)
                otherParentNodes.remove(otherParentNode)
                break
        for optionsMenuName in optionsMenuNames:
            cmds.optionMenu(optionsMenuName, edit=True, sl=1)


#this function will create a new vaild namespace and then duplicate everything in the current scene into the new namespace
def duplicateScene():
    global defaultNamespaceName, userCurrentNameSpace
    userCurrentNameSpace = cmds.namespaceInfo(currentNamespace=True)
    #find a new vaild namespace name
    nameSpaceCount = 0
    while cmds.namespace(exists=defaultNamespaceName + str(nameSpaceCount)):
        nameSpaceCount = nameSpaceCount + 1
    cmds.namespace(add=defaultNamespaceName + str(nameSpaceCount))
    DuplicateScene = ""
    #list objects only in the users current namespace
    cmds.namespace(set=userCurrentNameSpace)
    cmds.namespace(relativeNames=False)
    DuplicateScene = cmds.ls(userCurrentNameSpace+":*", long=True, objectsOnly=True)
    cmds.namespace(set=defaultNamespaceName + str(nameSpaceCount))
    cmds.select(DuplicateScene)
    DuplicateScene = cmds.duplicate(inputConnections=True, upstreamNodes=True, renameChildren=True)
    cmds.namespace(set=userCurrentNameSpace)
    return defaultNamespaceName + str(nameSpaceCount)


#returns true if there is at least one joint in the scene
#allows graceful failure if user accidentally runs script on an empty scene
def checkForExportablePfhorSkeleton():
    if not cmds.ls(type="joint"):
        print ""
        print ""
        print "** Script Output: **"
        print "** Scene contains no skeleton to be exported."
        return False
    else:
        return True
    
        
def exportFBX(*args):
    global optionsMenuNames, labelNames, fixOptions, minTime, maxTime, userCurrentNameSpace, globalControlCurveName
    rootJointName = ""
    skeleton = cmds.optionMenu("skeletonSel", q=True, v=True)
    rootJointName = skeleton
    if cmds.ls(rootJointName+"_ex") or cmds.ls(":Pfhor_root_transform"):
        cmds.confirmDialog(title='Error: Temporary Skeleton(s) still in Scene', message='Delete all temporary skeletons in the scene before attempting to bake again. Temporary skeletons have the suffix "_ex" and are grouped under the group "Pfhor_root_transform"')
        cmds.select(":Pfhor_root_transform")
        return
    if not checkForExportablePfhorSkeleton():
        return
    userCurrentNameSpace = cmds.namespaceInfo(currentNamespace=True)
    #make sure we are not in a namespace that we created to hold duplicates
    if userCurrentNameSpace.startswith(defaultNamespaceName):
        cmds.namespace(set=":")
    DuplicateSceneNameSpace = duplicateScene()
    cmds.namespace(set=DuplicateSceneNameSpace)
    skeleton = DuplicateSceneNameSpace + ":" + skeleton
    
    for optionsMenuName in optionsMenuNames:
        optionValue = cmds.optionMenu(optionsMenuName, q=True, v=True)
        #if adding to hierarchy
        if optionValue == fixOptions[1]:
            cmds.parent(DuplicateSceneNameSpace + ":" + labelNames[optionsMenuName], skeleton)
            parented[DuplicateSceneNameSpace + ":" + labelNames[optionsMenuName]] = skeleton
            
    
    #find all control curves under the skeleton that have at least one joint as a descendent
    #or if the transform node of that control curve has a joint as a descendent
    # childrenAdded = []
    # childCurves = cmds.listRelatives(skeleton, allDescendents=True, type="nurbsCurve", fullPath=True)
    # if childCurves:
        # for childCurve in childCurves:
            # parent = cmds.listRelatives(childCurve, parent=True, fullPath=True)[0]
            # if cmds.nodeType(parent) == "transform":
                # childJoints = cmds.listRelatives(parent, allDescendents=True, fullPath=True, type="joint")
                # if childJoints:
                    # for childJoint in childJoints:
                        # if childJoint not in childrenAdded:
                            # childrenAdded.append(childJoint)
                            # if cmds.ls(globalControlCurveName):
                                # parentString = cmds.listRelatives(childJoint, parent=True, fullPath=True)[0]
                                # parent = parentString.split(r'|')[2]
                            # else:
                                # parent = cmds.listRelatives(childJoint, parent=True, fullPath=True)[0]
                            # childName = childJoint.split(r'|')[-1]
                            # parentName = parent.split(r'|')[-1]
                            # print "childName = " + childName
                            # print "parentName = " + parentName
                            # cmds.parent(childJoint, skeleton)
                            # cmds.parentConstraint(parentName, childName, maintainOffset=True)
    
    
    relatives = cmds.listRelatives(skeleton, allDescendents=True, type="joint")
    relatives.append(skeleton)
    cmds.select(relatives)
    timeLU = (minTime, maxTime)
    
    cmds.bakeResults(relatives, simulation=True, time=timeLU, sampleBy=1, disableImplicitControl=False, preserveOutsideKeys=True, sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=True, shape=True)
    cmds.select(clear=True)
    
    allNodes = set(cmds.listRelatives(skeleton, allDescendents=True, fullPath=True))
    joints = set(cmds.listRelatives(skeleton, allDescendents=True, type="joint", fullPath=True))
    unwantedNodes = allNodes.difference(joints)
    for unwantedNode in unwantedNodes:
        if cmds.objExists(unwantedNode):
            cmds.delete(unwantedNode)
            
    # for joint in joints_to_delete_after_baking:
        # if cmds.objExists(DuplicateSceneNameSpace + ":" + joint):
            # cmds.delete(DuplicateSceneNameSpace + ":" + joint)
                
    #delete everything in new namespace that is not needed. note this deletes transform nodes!
    jointsToDelete = ["transform", "nurbsCurve"]
    for namespaceNode in cmds.namespaceInfo(DuplicateSceneNameSpace, ls=True, absoluteName=True):
        if cmds.objExists(namespaceNode):
            if cmds.nodeType(namespaceNode) in jointsToDelete:
                if not cmds.ls(globalControlCurveName):
                    cmds.delete(namespaceNode)
                else:
                    if namespaceNode != ":" + DuplicateSceneNameSpace + ":" + globalControlCurveName:
                        cmds.delete(namespaceNode)
    
    #select the new duplicated skeleton in the new namespace
    if cmds.ls(globalControlCurveName):
        skeleton = DuplicateSceneNameSpace + ":" + globalControlCurveName
    cmds.select(skeleton, hi=True)
    restoreJointNames(globalControlCurveName, DuplicateSceneNameSpace, rootJointName)
    

def restoreJointNames(globalControlCurveName, DuplicateSceneNameSpace, rootJointName):
    joints = cmds.ls(selection=True, type="joint")
    if cmds.ls(globalControlCurveName):
        cmds.rename(DuplicateSceneNameSpace+":"+globalControlCurveName, ":Pfhor_root_transform")
    for joint in joints:
        newName = joint.split(r':')[-1]
        if newName in joints_to_delete_after_baking:
            if cmds.objExists(joint):
                cmds.delete(joint)
        elif newName == rootJointName:
            cmds.rename(joint, ":"+rootJointName+"_ex")
        else:    
            cmds.rename(joint, ":"+newName+"_ex")
  
    
    
#===========================================================================================================
#export proccess for creating ref pose:
#'waist_spine_joint' and 'chest_spine_joint' must be removed\
#0)set time-slider to 1
#1)delete all keys off 'Shoulder_CNTRL'
#2)set 'Shoulder_CNTRL' R channel to 0
#3)re-parent 'chest_spine_joint' under 'Pfhor_Root_JNT'
#4)delete 'Shoulder_CNTRL'
#5)delete all keys off 'Master_Hip_CNTRL'
#6)delete all keys off 'Waist_CNTRL'
#7)delete all keys off 'HIP_CNTRL'
#8)re-parent 'waist_spine_joint' under 'Pfhor_Root_JNT'
#9)set 'Master_Hip_CNTRL' TR channels to 0
#10)delete 'Master_Hip_CNTRL'
#11)delete 'Spine_Curve'
#12)delete 'Spine_Handle1'
#13)delete 'Staff_01'
#14)delete 'left_arm_space_grp'
#15)delete all keys off 'R_Foot_CNTRL'
#16)set 'R_Foot_CNTRL' TR, 'R_toe_Curl', and 'R_foot_Roll' channels to 0
#17)delete 'R_Foot_CNTRL'
#18)delete all keys off 'L_Foot_CNTRL'
#19)set 'L_Foot_CNTRL' TR, 'L_toe_Curl', and 'L_foot_Roll' channels to 0
#20)delete 'L_Foot_CNTRL'
#21)delete all keys off 'L_ARM_CNTRL'
#22)set 'L_ARM_CNTRL' TR channels to 0
#23)delete 'L_ARM_CNTRL'
#22)delete all keys off 'R_ARM_CNTRL'
#23)set 'R_ARM_CNTRL' TR channels to 0
#24)delete 'R_ARM_CNTRL'
#25)delete 'ctrl_Character1_LeftShoulder'
#26)delete 'ctrl_Character1_RightShoulder'
#27)delete 'ctrl_Character1_Head'
#28)delete 'ctrl_Character1_Neck'
#29)delete 'ctrl_Character1_LeftForeArmRoll'
#30)delete 'ctrl_Character1_LeftHand'
#31)delete 'ctrl_Character1_RightForeArmRoll'
#32)delete 'ctrl_Character1_RightHand'
#33)delete 'ctrl_Character1_LeftHandThumb3'
#34)delete 'ctrl_Character1_LeftHandThumb2'
#35)delete 'ctrl_Character1_LeftHandMiddle3'
#36)delete 'ctrl_Character1_LeftHandMiddle2'
#37)delete 'ctrl_Character1_LeftHandMiddle1'
#38)delete 'ctrl_Character1_LeftHandPinky3'
#39)delete 'ctrl_Character1_LeftHandPinky2'
#40)delete 'ctrl_Character1_LeftHandPinky1'
#41)delete 'ctrl_Character1_RightHandThumb3'
#42)delete 'ctrl_Character1_RightHandThumb2'
#43)delete 'ctrl_Character1_RightHandMiddle3'
#44)delete 'ctrl_Character1_RightHandMiddle2'
#45)delete 'ctrl_Character1_RightHandMiddle1'
#46)delete 'ctrl_Character1_RightHandPinky3'
#47)delete 'ctrl_Character1_RightHandPinky2'
#48)delete 'ctrl_Character1_RightHandPinky1'
#49)delete 'effector1'
#50)delete 'effector2'
#51)delete 'effector3'
#52)delete 'effector4'
#53)delete 'effector5'
#54)delete 'effector6'
#55)delete 'effector7'
#56)delete 'effector8'
#57)delete 'effector9'
#58)delete 'waist_spine_joint'
#59)delete 'chest_spine_joint'
#60)delete 'L_arm_ROT'
#61)delete 'R_arm_ROT'
#62)delete 'L_leg_ROT'
#63)delete 'R_leg_ROT'
#64)delete 'grpZero'
#65)delete 'PhysX'
#66)unparent 'armbands'
#67)delete all non-deformer history of 'armbands'
#68)triangulate mesh 'armbands'
#69)unparent 'goggles'
#70)delete all non-deformer history of 'goggles'
#71)triangulate mesh 'goggles'
#72)unparent 'leg_armor'
#73)delete all non-deformer history of 'leg_armor'
#74)triangulate mesh 'leg_armor'
#75)unparent 'skirt_cloth'
#76)delete all non-deformer history of 'skirt_cloth'
#77)triangulate mesh 'skirt_cloth'
#78)unparent 'Pfhor_fighter_body'
#79)delete all non-deformer history of 'Pfhor_fighter_body'
#80)triangulate mesh 'skirt_cloth'
#81)unparent 'chest_armor'
#82)delete all non-deformer history of 'chest_armor'
#83)triangulate mesh 'chest_armor'
#84)unparent 'shoulder_pads'
#85)delete all non-deformer history of 'shoulder_pads'
#86)triangulate mesh 'shoulder_pads'
#87)delete 'pfhor_fighter_mesh_GRP'
#88)set 'Character1_LeftArm' R channels to 0
#89)set 'Character1_RightArm' R channels to 0
#90)set 'Character1_LeftForeArm' R channels to 0
#91)set 'Character1_LeftHand' R channels to 0
#92)set 'Character1_LeftForeArmRoll' R channels to 0
#93)set 'Character1_RightForeArm' R channels to 0
#94)set 'Character1_RightForeArmRoll' R channels to 0
#95)set 'Character1_RightHand' R channels to 0
#96)delete 'L_Shoulder'
#97)delete 'R_Shoulder'
#98)optimize scene size
#99)export all (Smoothing Groups=True, Tangents and Binormals=True, Animation=True, Bake Animation=False, Deformed Models=True, Skins=True, Blend Shapes=True)
#   You will get the following Skin Definition Warning:
#       The plug-in has found the following skin definition problems : 
#       Unable to find the bind pose for :  / Pfhor_Root_JNT. Use the DAG node current transform.


#options when importing refPose into UE4 as SKMesh
#1)Normals = Import Normals and Tangents
#2)Use Time 0 Pose for Ref Pose = True
#3)Preserve Smoothing Groups = True
#4)Import Meshes in Bone Hierarchy = True
#5)Import Animation = False
#6)Import Rigid Mesh = False
#7)Import LODs = False (import them separately)


#exporting anims process
#1)select all by type "joints"
#2)bake simulation (default options)
#3)delete all by type "nurbsCurve"
#4)delete 'L_Shoulder'
#5)delete 'R_Shoulder'