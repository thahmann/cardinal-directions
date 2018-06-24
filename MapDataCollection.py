import arcpy,os,sys,math,collections

#Collects the shared borders between objects
#Has two entries for each border. One from each object.
##inpShape - name of a shapefile of polygons
##outFC - name of an empty feature class of lines
def collectIntersections(inpShape,outFC):
    arcpy.env.workspace = homeFolder
    try:
        inFeatures = [inpShape]
        intersectOutput = outFC
        arcpy.Intersect_analysis(inFeatures,intersectOutput,"","","LINE")
    except Exception as err:
        print(err.args[0])

#Erases all of the elements in an ArcMap table
##tableCursor - arcpy.da.SearchCursor pointing into a table
def clearTable(tableCursor):
    with arcpy.da.UpdateCursor(tableCursor,"OBJECTID") as cursor:
        for row in cursor:
            cursor.deleteRow()           

#Collects the centroid of each polygon
#Not used in data processing, but is nice to look at
##inpShape - name of a shapefile of polygons
##inpColName - column in above shapefile which names each polygon
##outTab - table where mass centers will be stored
##outColName - column in above table where names will be stored
##clearBool - False appends data to output table, True clears the table first
def collectMassCenters(inpShape,inpColName,outTab,outColName,clearBool = False):
    cf = os.path.join(homeFolder,inpShape)
    from_crs = arcpy.da.SearchCursor(cf,["Shape@XY",inpColName])
    mc = os.path.join(homeFolder,outTab)
    mc_keys = [outcolName,"Midpoint_X","Midpoint_Y"]
    to_crs = arcpy.da.InsertCursor(mc,mc_keys)
    if(clearBool):
        clearTable(mc)
    for row in from_crs:
        print row[0]
        pt = row[0]
        to_crs.insertRow([row[1],pt[0],pt[1]])

#For two crossing lines, decides whether or not it forms a bubble
#An even number of crossings implies a bubble
def countCrosses(baseLine,detailLine):
    if(baseLine.disjoint(detailLine)):
        print "Bad input to countCrosses. No crossing."
        return None
    myDif = detailLine.difference(baseLine)
    pts = baseLine.intersect(myDif,1)
    if(pts.pointCount%2==0):
        return "bubble"
    else:
        return "partial"

#Given two points, calculates the angle from one to the other in radians
def polar_ang(origin_x,origin_y,pt_x,pt_y):
    dx = pt_x - origin_x
    dy = pt_y - origin_y
    ang = math.atan2(dy,dx)
    if(ang<0):
        ang += 2*math.pi
    return math.degrees(ang)

#From each object, breaks the surrounding area into 16 sectors and collects
#    what things are in each sector.
#Data collected is in the form: ReferenceObj, TargetObj, Dir, MidAngle
##inpShape - name of a shapefile of polygons
##inpColName - column in above shapefile which names each polygon
##inpFC - name of feature class containing shared borders between polygons
##outTab - name of table where the data will be written
##clearBool - False appends data to output table, True clears the table first
def collectSectors(inpShape,inpColName,inpFC,outTab,clearBool = False):
    polyFN = os.path.join(homeFolder,inpShape)
    poly_crs = arcpy.da.SearchCursor(polyFN,["Shape@","Shape@XY",inpColName])
    borders = os.path.join(homeFolder,inpFC)
    sectors = os.path.join(homeFolder,outTab)
    sector_keys = ["ReferenceObj","TargetObj","Dir","MidAngle"]
    sector_crs = arcpy.da.InsertCursor(sectors,sector_keys)
    if(clearBool):
        clearTable(sectors)
    for poly_row in poly_crs:
        center = poly_row[1]
        cx = center[0]
        cy = center[1]
        extent = poly_row[0].extent
        box = max(cx - extent.XMin,extent.XMax - cx,
                  cy - extent.YMin,extent.YMax - cy)+1
        PTS = []
        C = arcpy.Point(cx,cy)#Center
        PTS.append(arcpy.Point(cx+box,cy))#E 
        PTS.append(arcpy.Point(cx+box,cy+box*0.4142))#ENE
        PTS.append(arcpy.Point(cx+box,cy+box))#NE
        PTS.append(arcpy.Point(cx+box*0.4142,cy+box))#NNE
        PTS.append(arcpy.Point(cx,cy+box))#N
        PTS.append(arcpy.Point(cx-box*0.4142,cy+box))#NNW
        PTS.append(arcpy.Point(cx-box,cy+box))#NW
        PTS.append(arcpy.Point(cx-box,cy+box*0.4142))#WNW
        PTS.append(arcpy.Point(cx-box,cy))#W
        PTS.append(arcpy.Point(cx-box,cy-box*0.4142))#WSW
        PTS.append(arcpy.Point(cx-box,cy-box))#SW
        PTS.append(arcpy.Point(cx-box*0.4142,cy-box))#SSW
        PTS.append(arcpy.Point(cx,cy-box))#S
        PTS.append(arcpy.Point(cx+box*0.4142,cy-box))#SSE
        PTS.append(arcpy.Point(cx+box,cy-box))#SE
        PTS.append(arcpy.Point(cx+box,cy-box*0.4142))#ESE
        PTS.append(arcpy.Point(cx+box,cy))#E (again)
        DIR = ["EENE","NENE","ENNE","NNNE","NNNW","WNNW","NWNW","WWNW",
               "WWSW","SWSW","WSSW","SSSW","SSSE","ESSE","SESE","EESE"]
        UNKNOWN = [x+"-all" for x in DIR]
        #UNKNOWN is used to capture what sections of various sectors
        #    have not been described. This allows us to get a more
        #    complete understanding of underdefined areas.
        POLY = []
        for i in range(len(PTS)-1):
            POLY.append(arcpy.Polygon(arcpy.Array([C,PTS[i],PTS[i+1],C])))
        LINES = []
        for i in range(len(PTS)):
            LINES.append(arcpy.Polyline(arcpy.Array([C,PTS[i]])))
        borders_crs = arcpy.da.SearchCursor(borders,["Shape@",inpColName])
        border_row = borders_crs.next()
        while border_row:
            #Assumes that there are two copies of each border object,
            #    one from each object on the shared border. 
            br1 = border_row
            border_row = borders_crs.next()
            br2 = border_row
            if(poly_row[2]==br2[1]):
                #Ensures that the current polygon shares its name with br1
                temp = br1
                br1 = br2
                br2 = temp
            if(poly_row[2]==br1[1]):
                for i in range(len(POLY)):
                    #LINES[i] is clockwise, LINES[1+1] is ccw
                    if(not POLY[i].disjoint(br1[0])):
                        temp_dir = DIR[i]
                        wholeness = "x"
                        if((not LINES[i].disjoint(br1[0])) and
                           (not LINES[i+1].disjoint(br1[0]))):
                            wholeness = "complete"
                            if(temp_dir+"-all" in UNKNOWN):
                                UNKNOWN.remove(temp_dir+"-all")
                            if(temp_dir+"-cw" in UNKNOWN):
                                UNKNOWN.remove(temp_dir+"-cw")
                            if(temp_dir+"-ccw" in UNKNOWN):
                                UNKNOWN.remove(temp_dir+"-ccw")
                            over = POLY[i].intersect(br1[0],2)
                            if(over.isMultipart):
                                wholeness = "hole"
                                midStr = temp_dir+"-"+str((i+0.5)*22.5)
                                UNKNOWN.append(midStr)
                                for partNum in range(over.partCount):
                                    part = arcpy.Polyline(over.getPart(partNum))
                                    if((not LINES[i].disjoint(part)) and
                                       (not LINES[i+1].disjoint(part))):
                                        wholeness = "complete"
                                        UNKNOWN.remove(midStr)
                                        break
                                    
                        else:
                            if(not ((not(LINES[i].disjoint(br1[0]))) or
                                    (not(LINES[i+1].disjoint(br1[0]))))):
                                wholeness = "inside"
                            elif(not (LINES[i].disjoint(br1[0]))):
                                wholeness = countCrosses(LINES[i],br1[0])
                                if(temp_dir+"-all" in UNKNOWN):
                                    UNKNOWN.remove(temp_dir+"-all")
                                    UNKNOWN.append(temp_dir+"-ccw")
                                if(temp_dir+"-cw" in UNKNOWN):
                                    UNKNOWN.remove(temp_dir+"-cw")
                            else:
                                wholeness = countCrosses(LINES[i+1],br1[0])
                                if(temp_dir+"-all" in UNKNOWN):
                                    UNKNOWN.remove(temp_dir+"-all")
                                    UNKNOWN.append(temp_dir+"-cw")
                                if(temp_dir+"-ccw" in UNKNOWN):
                                    UNKNOWN.remove(temp_dir+"-ccw")
                        mid = br1[0].positionAlongLine(0.50,True)[0]
                        midAng = int(polar_ang(C.X,C.Y,mid.X,mid.Y))
                        wholeness += "-"+str(midAng)#Not used anymore
                        sector_crs.insertRow([br1[1],br2[1],temp_dir,str(midAng)])
                        
            try:
                border_row = borders_crs.next()
            except StopIteration:
                break
        #Converts the representation in UNKNOWN to a more definitive one
        if(len(UNKNOWN)>0):
            if(len(UNKNOWN)==1):
                parts = UNKNOWN[0].split("-")
                #sector_crs.insertRow([poly_row[2],"Unknown",parts[0],"inside-"+parts[1]])
                sector_crs.insertRow([poly_row[2],"Unknown",parts[0],parts[1]])
            else:
                start = -1
                end = -1
                for i in range(len(UNKNOWN)):
                    if("-cw" in UNKNOWN[i]):
                        end = DIR.index(UNKNOWN[i][:4])
                    elif("-ccw" in UNKNOWN[i]):
                        start= DIR.index(UNKNOWN[i][:4])
                if(end<start):
                    end += 15
                midAng = (int)(((((start+end)/2.0)+0.5)*22.5)%360)
                while(len(UNKNOWN)>0):
                    parts = UNKNOWN[0].split("-")
                    sector_crs.insertRow([poly_row[2],"Unknown", parts[0],str(midAng)])
                    #if(parts[1]=="all"):
                    #    sector_crs.insertRow([poly_row[2],"Unknown", parts[0],"complete-"+str(midAng)])
                    #else:
                    #    sector_crs.insertRow([poly_row[2],"Unknown", parts[0],"partial-"+str(midAng)])
                    del UNKNOWN[0]

#Converts a set of sixteenths into the smallest possible set of most 
#    granular sectors. This function is lossless in terms of the set
#    of sixteenths.
##labelSet - A list of sector names, in counterclockwise order
def aggregate(labelSet):
    allLabels = ["E","EENE","ENE","NENE","NE","ENNE","NNE","NNNE",
                 "N","NNNW","NNW","WNNW","NW","NWNW","WNW","WWNW",
                 "W","WWSW","WSW","SWSW","SW","WSSW","SSW","SSSW",
                 "S","SSSE","SSE","ESSE","SE","SESE","ESE","EESE"]
    if(len(labelSet)==1):
        return labelSet
    #Every pair of sixteenths becomes an eighth
    ##[NNNE-16,NNNW-16] -> N-8
    eighths = []
    eighthsCopy = [] #Collects eighths which do not get aggregated further
    for i in range(1,len(labelSet)):
        midLabel = allLabels[allLabels.index(labelSet[i].split("-")[0])-1]
        eighths.append(midLabel+"-8")
        eighthsCopy.append(midLabel+"-8")
    if(len(eighths)<=2):
        return eighths
    #Eligible groups of three eighths become a quarter
    ##[ENE-8,NE-8,NNE-8] -> NE-4
    ##[NE-8,NNE-8,N-8] -> No change. NNE-4 is invalid.
    adj = 0
    if(len(eighths[0].split("-")[0])<3):
        #The first eighth is ineligible to start a quarter, so we skip it
        adj = 1
    quarts = []
    for i in range(2+adj,len(eighths),2):#Every other eighth is eligible
        quarts.append(eighths[i-1].split("-")[0]+"-4")
        for j in range(3):
            if(eighths[i-j] in eighthsCopy):
                del eighthsCopy[eighthsCopy.index(eighths[i-j])]
    if(len(quarts)<3):
        if(adj==0):
            return quarts+eighthsCopy
        else:
            return eighthsCopy+quarts
    #Groups of three quarters become a half
    ##[NE-4,N-4,NW-4] -> N-2
    halves = []
    for i in range(2,len(quarts)):
        halves.append(quarts[i-1].split("-")[0]+"-2")
    return halves

#Converts a set of sixteenths into a counterclockwise ordered list 
##sectorSet - A set of sector names
##fourLetter - Toggles between the two hierarchies of sixteenths
##firstKey - Allows the specification of the most clockwise label if it
##               is known to speed up execution
def sortSet(sectorSet,fourLetter=True,firstKey="x"):
    sectorPoss = ['E','ENE','NE','NNE','N','NNW','NW','WNW',
                  'W','WSW','SW','SSW','S','SSE','SE','ESE']
    if(fourLetter):
        sectorPoss = ["EENE","NENE","ENNE","NNNE","NNNW","WNNW","NWNW","WWNW",
                      "WWSW","SWSW","WSSW","SSSW","SSSE","ESSE","SESE","EESE"]
    for sect in sectorSet:
        if sect not in sectorPoss:
            #Breaks if sectors are not collected correctly
            return sectorSet
    ccwInd = 0
    cwInd = 0
    inRange = False
    #left/right considers list notation. Left = clockwise. 
    leftFound = False
    rightFound = False
    if(firstKey is not "x"):
        ccwInd = sectorPoss.index(firstKey)-len(sectorPoss)
        cwInd = ccwInd
        leftFound = True
        inRange = True
    while(not rightFound):
        if(not inRange):
            if(sectorPoss[ccwInd] in sectorSet):
                inRange = True
                ccwInd -= 1
            else:
                ccwInd += 1
                cwInd += 1
        elif(not leftFound):
            if(sectorPoss[ccwInd] not in sectorSet):
                leftFound = True
                ccwInd += 1
            else:
                if(ccwInd==len(sectorPoss)*-1):
                    rightFound = True
                else:
                    ccwInd -= 1
        else:
            if((sectorPoss[cwInd] not in sectorSet)
               or cwInd-ccwInd==len(sectorPoss)-1
               or cwInd==len(sectorPoss)-1):
                rightFound = True
                if(sectorPoss[cwInd] not in sectorSet):
                    cwInd -= 1
            else:
                cwInd += 1
    if(ccwInd<0):
        if(cwInd<-1):
            return sectorPoss[ccwInd:cwInd+1]
        elif(cwInd==-1):
            return sectorPoss[ccwInd:]
        else:
            return sectorPoss[ccwInd:]+sectorPoss[:cwInd+1]
    else:
        return sectorPoss[ccwInd:cwInd+1]

#Splits a sector label into a list of its size, its label, and a size index
def splitLabel(label):
    if("-2" in label):
        return ["2",label.split("-")[0],0]
    elif("-4" in label):
        return ["4",label.split("-")[0],1]
    elif("-8" in label):
        return ["8",label.split("-")[0],2]
    elif("-16" in label):
        return ["16",label.split("-")[0],3]
    return label

#Generalizes sets of aggregated labels into a single label.
##labelSet - dictionary where keys are target names and values are ordered
##               aggregated lists of sectors
##midAngs - dictionary where keys are target names and values are integers
##               representing the angle of the middle of the shared border
def generalize(labelSet,midAngs):
    #print "###PRE-MULTISET GEN:",labelSet
    sects = ["EENE","NENE","ENNE","NNNE","NNNW","WNNW","NWNW","WWNW",
             "WWSW","SWSW","WSSW","SSSW","SSSE","ESSE","SESE","EESE"]
    rays = ['E','ENE','NE','NNE','N','NNW','NW','WNW',
            'W','WSW','SW','SSW','S','SSE','SE','ESE']   
    sizeLabs = ["2","4","8","16"]
    #print "LS",labelSet
    for key,value in labelSet.iteritems():
        ################################################
        ##### BEGINNING OF MULTISET GENERALIZATION #####
        ################################################
        if(len(value)>1):
            cts = [0,0,0,0]
            grps = {"2":[],"4":[],"8":[],"16":[]}
            for longLab in value:
                longSplit = splitLabel(longLab)
                grps[longSplit[0]] += [longSplit[1]]
                cts[longSplit[2]] += 1
            """
            EIGHT CASES
            [2, 0, 0, 0] - give to half of shortest label
            [0, 2, 0, 0] - give to best half
            [0, 2, 1, 0] - give to best half
            [0, 2, 2, 0] - give to best half
            [0, 1, 1, 0] - quarter absorbs
            [0, 1, 2, 0] - quarter absorbs
            [0, 0, 2, 0] - give to best quarter
            [0, 0, 3, 0] - give to best quarter
            """
            for i in range(4):
                if(cts[i]>=2):
                    if(i==0):
                        shortLab = grps['2'][0]
                        for shortLabPoss in grps['2']:
                            if(len(shortLabPoss)<len(shortLab)):
                                shortLab = shortLabPoss
                        labelSet[key] = [shortLab+"-2"]
                        break
                    start = rays.index(grps[sizeLabs[i]][0])-math.pow(2,2-i)
                    end = (rays.index(grps[sizeLabs[i]][cts[i]-1])+math.pow(2,2-i))%16
                    if(start>end):
                        start -= 16
                    underSpan = []
                    for j in range((int)(start),(int)(end)):
                        underSpan += [sects[j]]
                    underCt = collections.Counter(underSpan)
                    upper = (int)(math.pow(2,4-i))
                    bestMatch = 0
                    bestLabel = ""
                    for j in range(14-upper,15-upper-16,-2):
                        upperSpan = []
                        for k in range(upper):
                            upperSpan += [sects[j+k]]
                        upperCt = collections.Counter(upperSpan)
                        intersection = (underCt & upperCt)
                        if(len(intersection)>bestMatch):
                            bestMatch = len(intersection)
                            bestLabel = "xxxx"
                        if(len(intersection)==bestMatch and
                           len(bestLabel)>len(rays[j])):
                            bestLabel = rays[j+(upper/2)]
                    finalLabel = bestLabel+"-"+sizeLabs[i-1]
                    labelSet[key] = [finalLabel]
                    break
                elif(cts[i]==1):
                    labelSet[key] = [grps[sizeLabs[i]][0]+"-"+sizeLabs[i]]
                    break
    #print "LS2",labelSet
    ###########################################
    ##### END OF MULTISET GENERALIZATION  #####
    ##### BEGINNING OF FORCING SIXTEENTHS #####
    ###########################################
    broadSet = []
    noBroad = []
    #revertable = []
    #revertSet = {}
    for key,value in labelSet.iteritems():
        broadLab = splitLabel(value[0])#Assumes set length 1
        if(broadLab[2]==3):
            labInd = sects.index(broadLab[1])
            newLab1 = rays[labInd]
            newLab2 = rays[(labInd+1)%16]
            labPair = [newLab1+"-8",newLab2+"-8"]
            labelSet[key] = labPair
            broadSet.append(key)
    ############################################
    #####    END OF FORCING SIXTEENTHS     #####
    ##### BEGINNING OF CONFLICT RESOLUTION #####
    ############################################
    resolving = True
    while(resolving):
        resolving = False
        ctLabs = {}#<label,target>
        ctTarg = {}#<target,number>
        confLabs = []
        confTarg = []
        ##### Count Number of Conflicts #####
        for key,value in labelSet.iteritems():
            ctTarg[key] = 0
            for lab in value:
                splitVal = splitLabel(lab)
                if(splitVal[1] not in ctLabs):
                    ctLabs[splitVal[1]] = [key]
                else:
                    resolving = True
                    ctLabs[splitVal[1]] += [key]
                    for tgt in ctLabs[splitVal[1]]:
                        ctTarg[tgt] += 1
                        if(tgt not in confTarg):
                            confTarg.append(tgt)
                    if(splitVal[1] not in confLabs):
                        confLabs.append(splitVal[1])
        if(resolving):
            reduced = False
            ##### Reduction #####
            for tgt in confTarg:
                for lab in labelSet[tgt]:
                    sl = splitLabel(lab)
                    if(len(ctLabs[sl[1]])==1):
                        reduced = True
                        labelSet[tgt] = [lab]
            forced = False
            ##### Forcing Perfectly Overlapped Sectors to Change #####
            if(not (reduced)):
                for tgt1 in confTarg:
                    if(not forced):
                        for tgt2 in confTarg:
                            if(labelSet[tgt1] == labelSet[tgt2] and
                               not (tgt1==tgt2) and
                               len(labelSet[tgt1])>=2):
                                forced = True
                                cpySet = labelSet[tgt1][:]
                                onBreak = False
                                if(abs(midAngs[tgt1]-midAngs[tgt2])>200):
                                    onBreak = True
                                if((midAngs[tgt1]>midAngs[tgt2] and not onBreak) or
                                   (midAngs[tgt1]<midAngs[tgt2] and onBreak)):
                                    hold = tgt1
                                    tgt1 = tgt2
                                    tgt2 = hold
                                tgt1Mid = midAngs[tgt1]
                                tgt2Mid = midAngs[tgt2]
                                if(onBreak):
                                    tgt2Mid += 360
                                if(len(labelSet[tgt1])==3):
                                    midSplit = splitLabel(labelSet[tgt1][1])
                                    midAng = rays.index(midSplit[1])*22.5
                                    if(onBreak and midAng<200):
                                        midAng += 360
                                    best = -1
                                    if(abs(midAng-tgt1Mid)<abs(midAng-tgt2Mid)):
                                        best = 0
                                    else:
                                        best = 1
                                    tgts = [tgt1,tgt2]
                                    labelSet[tgts[best]] = [cpySet[1]]
                                    labelSet[tgts[1-best]] = [cpySet[2-(2*best)]]
                                else:
                                    labelSet[tgt1] = [cpySet[0]]
                                    labelSet[tgt2] = [cpySet[1]]
                                broadSet.remove(tgt1)
                                broadSet.remove(tgt2)
                                noBroad.append(tgt1)
                                noBroad.append(tgt2)
                                break
            broadened = False
            ##### Broadening Generalization #####
            if(not (reduced or forced)):
                for tgt in confTarg:
                    if(tgt not in broadSet):
                        broadened = True
                        broadSet.append(tgt)
                        broadLab = splitLabel(labelSet[tgt][0])#Assumes length 1
                        labInd = rays.index(broadLab[1])
                        dist = (int)(math.pow(2,2-broadLab[2]))
                        newSize = "-"+sizeLabs[broadLab[2]-1]
                        labelSet[tgt] = [rays[labInd-dist]+newSize]+labelSet[tgt]
                        labelSet[tgt] += [rays[(labInd+dist)%16]+newSize]
            if(not (reduced or forced or broadened)):                
                print "Uncaught error. Sorry! Probably going to crash now."
                resolving = False
    ##### Reduce All Sets of Possibilities to Best Option #####
    for key,value in labelSet.iteritems():
        if(len(value)>1):
            ptr = -1
            minLab = 5
            for i in range(len(value)):
                sl = splitLabel(value[i])
                if(len(sl[1])<minLab):
                    minLab = len(sl[1])
                    ptr = i
            labelSet[key] = [labelSet[key][ptr]]
    #print "###POST-SINGLE GEN (final):",labelSet
    return labelSet

#Reads sectors in from memory, and aggregates and generalizes them.
##inpSectors - table created as per the collectSectors function
##fn - a filename where final output will be written
def simplifySectors(inpSectors,fn=None):
    allLabels = ["E","EENE","ENE","NENE","NE","ENNE","NNE","NNNE",
                 "N","NNNW","NNW","WNNW","NW","NWNW","WNW","WWNW",
                 "W","WWSW","WSW","SWSW","SW","WSSW","SSW","SSSW",
                 "S","SSSE","SSE","ESSE","SE","SESE","ESE","EESE"]
    sectors = os.path.join(homeFolder,inpSectors)
    sector_keys = ["ReferenceObj","TargetObj","Dir","MidAngle"]
    sector_crs = arcpy.da.SearchCursor(sectors,sector_keys)
    fOut = None
    fSpace = ""
    if(fn):
        fOut = open(fn,'w')
    finished=False #probably obsolete
    row = sector_crs.next()
    thisRef = row[0]
    lastRef = row[0]
    while(not finished):
        tgtSet = {}#target names:sets of dirs
        midAngs = {}#target name:center angle
        while(thisRef == row[0] and not finished):
            if(row[1] not in tgtSet):
                tgtSet[row[1]] = set([row[2]])
                midAngs[row[1]] = float(row[3])
            else:
                tgtSet[row[1]] = tgtSet[row[1]] | set([row[2]])
            try:
                row = sector_crs.next()
            except:
                finished = True
        if(fOut):
            fOut.write(fSpace+"##############Detailing: "+str(lastRef))
            fSpace = "\n\n"
        else:
            print ""
            print "##############Detailing:",lastRef
        #print "###PRE AGGREGATION:"
        for key,value in tgtSet.iteritems():
            ordered = sortSet(value)
            if(len(ordered)==1):
                tgtSet[key] = [ordered[0]+"-16"]
            else:
                newSet = []
                for i in range(len(ordered)):
                    newSet.append(ordered[i]+"-16")
                tgtSet[key] = newSet
            #print key,tgtSet[key]
            tgtSet[key] = aggregate(tgtSet[key])
            #print "...preparing to generalize..."
        #print "###POST AGGREGATION:"
        #for tgt in tgtSet:
        #    print tgt,tgtSet[tgt]
        #print "###midAngs:",midAngs
        genSet = generalize(tgtSet,midAngs)
        if(fOut):
            fOut.write("\n###POST GENERALIZATION:")
        else:
            print "###POST GENERALIZATION:"
        for tgt in genSet:
            if(fOut):
                fOut.write("\n"+str(tgt)+" "+str(genSet[tgt]))
            else:
                print tgt,genSet[tgt]
        #print "---------- Outputting relations for",lastRef,"----------"
        #print tgtSet
        thisRef = row[0]
        lastRef = thisRef

#This should be set to the filepath of your geodatabase
homeFolder = 'C:\Users\Greg\ArcGIS\Test.gdb'

if __name__ == '__main__':
    print "Starting!"
    #collectIntersections("Maine\Counties_Trimmed","Shared_Borders")
    #collectMassCenters("Maine\Counties_Trimmed","COUNTY","Mass_Centers","County",True)            
    #collectSectors("Maine\Counties_Trimmed","COUNTY","Shared_Borders","Intersect_Sectors_4",True)
    simplifySectors("Intersect_Sectors_4","ForTex_Ours2.txt")
    
    print "...Done..."
