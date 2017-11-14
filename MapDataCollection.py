import arcpy,os,sys,math

homeFolder = 'C:\Users\Greg\ArcGIS\Test.gdb'

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

#Collects the centroid of each polygon
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


#From each object, breaks the surrounding area into 8 sectors and collects
#    what things are in each sector
#Each sector is represented as the overlap between two major quarters
#    For example, the overlap between the N quarter and NE quarter is N,NE 
#Data collected is in the form: FromObject, ToObject, Dir, Completeness
#Completeness is any one of:
#    complete (The ToObject goes entirely through a sector
#    partial  (The ToObject goes partially through a sector. Additionally marked
#              clockwise or counterclockwise for which direction it exits)
#    inside   (Additionally marked with the angle to the center of the ToObject)
#    bubble   (The border of the ToObject enters and exits the sector on the
#              same side)
##inpShape - name of a shapefile of polygons
##inpColName - column in above shapefile which names each polygon
##inpFC - name of feature class containing shared borders between polygons
##outTab - name of table where the data will be written
##clearBool - False appends data to output table, True clears the table first
def findBorders(inpShape,inpColName,inpFC,outTab,clearBool = False):
    polyFN = os.path.join(homeFolder,inpShape)
    poly_crs = arcpy.da.SearchCursor(polyFN,["Shape@","Shape@XY",inpColName])
    borders = os.path.join(homeFolder,inpFC)
    sectors = os.path.join(homeFolder,outTab)
    sector_keys = ["FromObj","ToObj","Dir","Completeness"]
    sector_crs = arcpy.da.InsertCursor(sectors,sector_keys)
    if(clearBool):
        clearTable(sectors)
    for poly_row in poly_crs:
        center = poly_row[1]
        cx = center[0]
        cy = center[1]
        extent = poly_row[0].extent
        trp = max(extent.XMax-cx,extent.YMax-cy)
        tlp = max(cx-extent.XMin,extent.YMax-cy)
        blp = max(cx-extent.XMin,cy-extent.YMin)
        brp = max(extent.XMax-cx,cy-extent.YMin)
        C = arcpy.Point(cx,cy)
        TR = arcpy.Point(cx+trp,cy+trp)
        TC = arcpy.Point(cx,extent.YMax)
        TL = arcpy.Point(cx-tlp,cy+tlp)
        CL = arcpy.Point(extent.XMin,cy)
        BL = arcpy.Point(cx-blp,cy-blp)
        BC = arcpy.Point(cx,extent.YMin)
        BR = arcpy.Point(cx+brp,cy-brp)
        CR = arcpy.Point(extent.XMax,cy)
        PTS = [TR,TC,TL,CL,BL,BC,BR,CR,TR]
        DIR = ["N,NE","N,NW","W,NW","W,SW","S,SW","S,SE","E,SE","E,NE"]
        UNKNOWN = [x+"-CW" for x in DIR]+[x+"-CCW" for x in DIR]
        POLY = []
        for i in range(len(PTS)-1):
            POLY.append(arcpy.Polygon(arcpy.Array([C,PTS[i],PTS[i+1],C])))
        LINES = []
        for i in range(len(PTS)):
            LINES.append(arcpy.Polyline(arcpy.Array([C,PTS[i]])))
        borders_crs = arcpy.da.SearchCursor(borders,["Shape@",inpColName])
        border_row = borders_crs.next()
        while border_row:
            br1 = border_row
            border_row = borders_crs.next()
            br2 = border_row
            if(poly_row[2]==br2[1]):
                temp = br1
                br1 = br2
                br2 = temp
            if(poly_row[2]==br1[1]):
                for i in range(len(POLY)):
                    if(not POLY[i].disjoint(br1[0])):
                        temp_dir = DIR[i]
                        wholeness = "x"
                        if((not LINES[i].disjoint(br1[0])) and
                           (not LINES[i+1].disjoint(br1[0]))):
                            wholeness = "complete"
                            try:
                                UNKNOWN.remove(temp_dir+"-CW")
                            except:
                                pass
                            try:
                                UNKNOWN.remove(temp_dir+"-CCW")
                            except:
                                pass
                            over = POLY[i].intersect(br1[0],2)
                            if(over.isMultipart):
                                wholeness = "hole"
                                UNKNOWN.append(temp_dir+"-C")
                                for partNum in range(over.partCount):
                                    part = arcpy.Polyline(over.getPart(partNum))
                                    if((not LINES[i].disjoint(part)) and
                                       (not LINES[i+1].disjoint(part))):
                                        wholeness = "complete"
                                        UNKNOWN.remove(temp_dir+"-C")
                                    
                        else:
                            if(not ((not(LINES[i].disjoint(br1[0]))) or
                                    (not(LINES[i+1].disjoint(br1[0]))))):
                                wholeness = "inside"
                                mid = br1[0].positionAlongLine(0.50,True)[0]
                                midAng = int(polar_ang(C.X,C.Y,mid.X,mid.Y))
                                wholeness += "-"+str(midAng)
                            elif(not (LINES[i].disjoint(br1[0]))):
                                wholeness = countCrosses(LINES[i],br1[0])
                                wholeness += "-cw"
                                try:
                                    UNKNOWN.remove(temp_dir+"-CW")
                                except:
                                    pass
                            else:
                                wholeness = countCrosses(LINES[i+1],br1[0])
                                wholeness += "-ccw"
                                try:
                                    UNKNOWN.remove(temp_dir+"-CCW")
                                except:
                                    pass
                        sector_crs.insertRow([br1[1],br2[1],temp_dir,wholeness])
                        
            try:
                border_row = borders_crs.next()
            except StopIteration:
                break
        while(len(UNKNOWN)>0):
            parts = UNKNOWN[0].split("-")
            if(parts[1]=="C"):
                sector_crs.insertRow([poly_row[2],"Unknown",
                                     parts[0],"inside-?"])
            elif(parts[1]=="CW"):
               used = False
               for others in UNKNOWN[1:]:
                   if(("CCW" in others) and (parts[0] in others)):
                       sector_crs.insertRow([poly_row[2],"Unknown",
                                            parts[0],"complete"])
                       used = True
                       UNKNOWN.remove(others)
                       break
               if(not used):
                   sector_crs.insertRow([poly_row[2],"Unknown",
                                        parts[0],"partial-cw"])
            elif(parts[1]=="CCW"):
                sector_crs.insertRow([poly_row[2],"Unknown",
                                     parts[0],"partial-ccw"])
            del UNKNOWN[0]
    
##inpSectors - file created as per the findBorders function
def objectsAndDirections(inpSectors,clearBool=False):
    sectors = os.path.join(homeFolder,inpSectors)
    sector_keys = ["FromObj","ToObj","Dir","Completeness"]
    sector_crs = arcpy.da.SearchCursor(sectors,sector_keys)
    labelSet = {'N':set(),'E':set(),'S':set(),'W':set(),
                'NE':set(),'SE':set(),'SW':set(),'NW':set()}
    undecidedLabels = ['N','NE','E','SE','S','SW','W','NW']
    unusedObjects = []
    objectSet = {}
    objectCCW = {}
    insides = {}
    duals = []
    finished = False        
    row = sector_crs.next()
    currentObject = row[0]
    while(not finished):
        ########## PART 1: RETRIEVING THE MINED INFORMATION ##########
        # Just loading the information into memory.                  #
        # Collecting and ordering the sectors that each section of   #
        #   border passes through, as well as the center angles for  #
        #   those inside a sector.                                   #
        ##############################################################
        print "----- Reference object:",currentObject,"-----"
        while(row[0]==currentObject):
            if(row[1] not in objectSet):
                objectSet[row[1]] = set(row[2].split(","))
                unusedObjects.append(row[1])
            else:
                objectSet[row[1]] = objectSet[row[1]] | set(row[2].split(","))
            if("inside" in row[3]):
                insides[row[1]]=row[3].split("-")[1]
            if("partial-ccw" in row[3]):
                sp = row[2].split(",")
                if(clockwiseRot(sp[0])==sp[1]):
                    objectCCW[row[1]]=sp[1]
                else:
                    objectCCW[row[1]]=sp[0]
            try:
                row = sector_crs.next()
            except:
                row = ["x"]
                print "cS1:",objectSet
        for key,value in objectSet.iteritems():
            if(key in objectCCW):
                objectSet[key] = sortSet(value,objectCCW[key])
            else:
                objectSet[key] = sortSet(value)
        ############### PART 2: FIRST-PASS ASSIGNMENTS ###############
        # Assigns to each object the label in the center of its      #
        #   range.                                                   #
        # Keeps track of which objects got two labels.               #
        ##############################################################
        for key,value in objectSet.iteritems():
            if(len(value)%2==0):
                if(len(value)==2):
                    label = value[int((int(insides[key])%45)/22.5)]
                    labelSet[label] |= set([key])
                    try:
                        undecidedLabels.remove(label)
                    except:
                        pass
                else:
                    duals.append(key)
                    labelSet[value[len(value)/2]] |= set([key])
                    labelSet[value[(len(value)/2)-1]] |= set([key])
                    try:
                        undecidedLabels.remove(value[(len(value)/2)-1])
                    except:
                        pass
                    try:
                        undecidedLabels.remove(value[len(value)/2])
                    except:
                        pass
            else:
                labelSet[value[len(value)/2]] |= set([key])
                try:
                    undecidedLabels.remove(value[len(value)/2])
                except:
                    pass
            try:
                unusedObjects.remove(key)
            except:
                pass
        ################## PART 3: RESOLVE CONFLICTS #################
        # Rule 1: When two objects are within a single sector, we    #
        #         must increase granularity and grant the new label  #
        #         to the object closest to the midpoint.             #
        # Rule 2: Duals concede one of their labels if there another #
        #         object whch lays claim to it.                      #
        # Rule 3: Gives precidence to objects which span multiple    #
        #         sectors over those entirely inside one.            #
        # Rule 4: Priority is given to objects for which the label   #
        #         is closer the center of their range of labels.     #
        ##############################################################
        fixing = True
        while(fixing):
            fixing = False
            try:
                for key,value in labelSet.iteritems():
                    value = list(value)
                    if(len(value)==2):
                        inVal = 0
                        if((value[0] in insides) and (value[1] in insides)):
                            full = True
                            for v in value:
                                for l in objectSet[v]:
                                    if(len(l)==0):
                                        full=False
                            if(full):
                                newLabel = objectSet[value[0]]
                                claimer = value[0]
                                if(abs(int(insides[value[1]])%45-22.5)<
                                   abs(int(insides[value[0]])%45-22.5)):
                                    newLabel = objectSet[value[1]]
                                    claimer = value[1]
                                if(len(newLabel[0])==1):
                                    newLabel = newLabel[0]+newLabel[1]
                                else:
                                    newLabel = newLabel[1]+newLabel[0]
                                labelSet[newLabel] = set([claimer])
                                labelSet[key].discard(claimer)
                                continue
                        if((value[0] in insides) and (value[1] in duals)):
                            value = [value[1],value[0]]
                        if((value[1] in insides) and (value[0] in duals)):
                            duals.remove(value[0])
                            labelSet[key].discard(value[0])
                            continue
                        if(value[1] in insides):
                            value = [value[1],value[0]]
                        if(value[0] in insides and value[1] not in insides):
                            newLabel = objectSet[value[0]]
                            if(len(newLabel[0])==1):
                                newLabel = newLabel[0]+newLabel[1]
                            else:
                                newLabel = newLabel[1]+newLabel[0]
                            labelSet[newLabel] = set([value[0]])
                            labelSet[key].discard(value[0])
                        else:
                            priority = 100000
                            claimer = "x"
                            lastfail = "x"
                            for v in value:
                                span = objectSet[v]
                                newPriority = abs((len(span)/2.0 - 0.5) - span.index(key))
                                if(newPriority<priority):
                                    priority = newPriority
                                    lastfail = claimer
                                    claimer = v
                                else:
                                    lastfail = v
                            if(lastfail in duals):
                                duals.remove(lastfail)
                                labelSet[key].discard(lastfail)
                            else:
                                priority = 100000
                                claimer = "x"
                                edge = True
                                span = objectSet[lastfail]
                                for l in span:
                                    newEdge = (span[0]==l or span[-1]==l)
                                    newPriority = abs((len(span)/2.0 - 0.5) - span.index(l))
                                    if(len(labelSet[l])==0):
                                        if(claimer=="x" or newPriority<priority or
                                           (newPriority==priority and edge==True and newEdge==False)):
                                            claimer = l
                                            edge = newEdge
                                            priority = newPriority
                                labelSet[claimer] |= set([lastfail])
                                labelSet[key].discard(lastfail)
                                undecidedLabels.remove(claimer)
            except:
                fixing = True
        ################ PART 4: USE REMAINING LABELS ################
        # Unused labels are given to whichever object has the lowest #
        #   priority for them.                                       #
        ##############################################################
        while(len(undecidedLabels)>0):
            l = undecidedLabels[0]
            claimer = "x"
            edge = True
            priority = 10000
            for myObject,span in objectSet.iteritems():
                if l in span:
                    newEdge = (span[0]==l or span[-1]==l)
                    newPriority = abs((len(span)/2.0 - 0.5) - span.index(l))
                    if(claimer=="x" or newPriority<priority or
                       (newPriority==priority and edge==True and newEdge==False)):
                        claimer = myObject
                        edge = newEdge
                        priority = newPriority
            labelSet[l] |= set([claimer])
            del undecidedLabels[0]
        print "lS",labelSet
        # End current object. Below here resets data structures for next loop.
        if(row[0] is not "x"):
            currentObject = row[0]
            labelSet = {'N':set(),'E':set(),'S':set(),'W':set(),
                'NE':set(),'SE':set(),'SW':set(),'NW':set()}
            undecidedLabels = ['N','NE','E','SE','S','SW','W','NW']
            unusedObjects = []
            objectSet = {}
            objectCCW = {}
            insides = {}
            duals = []
        else:
            finished = True
            

#Takes a set of sectors and organizes them into a counterclockwise list
#Mirrorring polar coordinates, E is first, when all elements are present
def sortSet(sectorSet,firstKey="x"):
    sectorPoss = ['E','NE','N','NW','W','SW','S','SE']
    ccwInd = 0
    cwInd = 0
    inRange = False
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
        
#Concatenates a list of strings into one large comma separated string
def compressRange(angRange):
    outStr = ""
    for ang in angRange:
        outStr += ang+","
    return outStr[:-1]

#Given two points, calculates the angle from one to the other in radians
def polar_ang(origin_x,origin_y,pt_x,pt_y):
    dx = pt_x - origin_x
    dy = pt_y - origin_y
    ang = math.atan2(dy,dx)
    if(ang<0):
        ang += 2*math.pi
    return math.degrees(ang)

#Erases all of the elements in an ArcMap table
def clearTable(tableCursor):
    with arcpy.da.UpdateCursor(tableCursor,"OBJECTID") as cursor:
        for row in cursor:
            cursor.deleteRow()

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

#Grabs the map axis 45 degrees clockwise of a given axis.
#Not efficint for finding ranges, but good in a pinch
def clockwiseRot(direction):
    if(direction=="N"):
        return "NE"
    elif(direction=="NE"):
        return "E"
    elif(direction=="E"):
        return "SE"
    elif(direction=="SE"):
        return "S"
    elif(direction=="S"):
        return "SW"
    elif(direction=="SW"):
        return "W"    
    elif(direction=="W"):
        return "NW"
    elif(direction=="NW"):
        return "N"

#collectIntersections("Maine\Counties_Trimmed","Shared_Borders")
#collectMassCenters("Maine\Counties_Trimmed","COUNTY","Mass_Centers","County",True)            
#findBorders("Maine\Counties_Trimmed","COUNTY","Shared_Borders","Intersect_Sectors_2",True)
objectsAndDirections("Intersect_Sectors_2",True)
