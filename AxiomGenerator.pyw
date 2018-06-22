#I think this is standard in a lot of languages
def listIndex(myList,obj):
    try:
        v = myList.index(obj)
    except ValueError:
        v = -1
    return v

#A single set of sectors that forms a full circle
class Hierarchy:
    def __init__(self,N,labelSet):
        self.N_Align = N
        self.Labels = labelSet

#Single logical statement
#Represented in a preorder format and can be printed in standard logical symbols
#   or in CL by changing a single argument. The parser is part of the class.
#Acceptable symbols and their syntax are as follows:
###          forall - [_F,[vars],[claim]]
###             iff - [_IFF,[left],[right]]
###              if - [_IF,[left],[right]]
###  unary function - [_FN,predicate,arg]
### binary function - [_BFN,predicate,arg1,arg2]
###              or - [_OR,[],...]
###             and - [_AND,[],...]
class Claim:
    def __init__(self,logic):
        self.L = logic

    #Useful in subsetting claims by those that mention a certain hierarchy
    def usesLabel(self,label,logic=None):
        if(logic==None):
            logic=self.L
        found=False
        for term in logic:
            if(type(term) is str):
                found = found | (term==label)
            else:
                found = found | self.usesLabel(label,term)
        return found

    #Turns the claim from its preorder format to the format desired
    ##logic - allows the parser to be recursive. A value of None uses the logic
    ##            of this claim
    ##flag - desired format. "plain"=standard symbols. "CL"=common logic.
    def parse(self,flag="plain",logic=None):
        if(logic==None):
            logic=self.L
        if(type(logic) is str):
            return logic
        if(logic[0]=="_F"):#[_F,[vars],[claim]]
            varstr = ""
            for v in logic[1]:
                varstr+=v+" "
            varstr = varstr[:-1]
            if(flag=="plain"):
                return "forall "+varstr+" ["+self.parse(flag,logic[2])+"]"
            else:
                return "\t"*flag+"(forall ("+varstr+")"+"\n"+self.parse(flag+1,logic[2])+"\n"+"\t"*flag+")"
        elif(logic[0]=="_IFF"):#[_IFF,[left],[right]]
            if(flag=="plain"):
                return self.parse(flag,logic[1])+" <--> "+self.parse(flag,logic[2])
            else:
                return "\t"*flag+"(iff\n"+self.parse(flag+1,logic[1])+"\n"+self.parse(flag+1,logic[2])+"\n"+"\t"*flag+")"
        elif(logic[0]=="_IF"):#[_IF,[left],[right]]
            if(flag=="plain"):
                return self.parse(flag,logic[1])+" --> "+self.parse(flag,logic[2])
            else:
                return "\t"*flag+"(if\n"+self.parse(flag+1,logic[1])+"\n"+self.parse(flag+1,logic[2])+"\n"+"\t"*flag+")"
        elif(logic[0]=="_FN"):#[_FN,predicate,arg]
            if(flag=="plain"):
                return logic[1]+"("+self.parse(flag,logic[2])+")"
            else:
                return "\t"*flag+"("+logic[1]+"\n"+self.parse(flag+1,logic[2])+"\n"+"\t"*flag+")"
        elif(logic[0]=="_BFN"):#[_BFN,predicate,arg1,arg2]
            if(flag=="plain"):
                return logic[1]+"("+self.parse(flag,logic[2])+","+self.parse(flag,logic[3])+")"
            else:
                return "\t"*flag+"("+logic[1]+"\n"+self.parse(flag+1,logic[2])+"\n"+self.parse(flag+1,logic[3])+"\n"+"\t"*flag+")"
        elif(logic[0]=="_OR"):#[_OR,[],...]
            if(flag=="plain"):
                outStr=""
                for i in range(1,len(logic)):
                    if(i>1):
                        outStr += " v "
                    outStr += self.parse(flag,logic[i])
                return outStr
            else:
                outStr="\t"*flag+"(OR\n"
                for term in logic[1:]:
                    outStr += self.parse(flag+1,term)+"\n"
                outStr+="\t"*flag+")"
                return str(outStr)
        elif(logic[0]=="_AND"):#[_AND,[],...]
            if(flag=="plain"):
                outStr=""
                for i in range(1,len(logic)):
                    if(i>1):
                        outStr += " ^ "
                    outStr += self.parse(flag,logic[i])
                return outStr
            else:
                outStr="\t"*flag+"(AND\n"
                for term in logic[1:]:
                    outStr += self.parse(flag+1,term)+"\n"
                outStr+="\t"*flag+")"
                return str(outStr)
        else:
            if(flag=="plain"):
                return str(logic[0])
            else:
                return "\t"*flag+str(logic[0])

HalfA = Hierarchy(True,["N","S"])
HalfB = Hierarchy(True,["E","W"])
HalfC = Hierarchy(False,["NE","SW"])
HalfD = Hierarchy(False,["NW","SE"])
QuarterA = Hierarchy(True,["NE","NW","SW","SE"])
QuarterB = Hierarchy(False,["E","N","W","S"])
EighthA = Hierarchy(True,["ENE","NNE","NNW","WNW","WSW","SSW","SSE","ESE"])
EighthB = Hierarchy(False,["E","NE","N","NW","W","SW","S","SE"])
SixteenthA = Hierarchy(False,["E","ENE","NE","NNE","N","NNW","NW","WNW",
                              "W","WSW","SW","SSW","S","SSE","SE","ESE"])
SixteenthB = Hierarchy(False,["EENE","NENE","ENNE","NNNE","NNNW","WNNW",
                              "NWNW","WWNW","WWSW","SWSW","WSSW","SSSW",
                              "SSSE","ESSE","SESE","EESE"])
AllHierarchies = [HalfA,HalfB,HalfC,HalfD,QuarterA,
                  QuarterB,EighthA,EighthB,SixteenthA,SixteenthB]
Sizes = {2:"Half",4:"Quarter",8:"Eighth",16:"Sixteenth"}

## The following 6 functions are shorthand used later ##
def po(size,dir):
    return ["_BFN","BCont",["x"],["_FN",size+dir,["x"]]]

def bc(dir1,dir2,size):
    return ["_F",["x"],["_BFN","BCont",["_FN","Ray"+dir1,["x"]],["_FN",size+dir2,["x"]]]]

def sc(dir1,dir2):
    return ["_F",["x"],["_BFN","SC",["_FN","Sixteenth"+dir1,["x"]],["_FN","Sixteenth"+dir2,["x"]]]]

def rd(dir1,dir2,size):
    return ["_F",["x"],["_BFN","\xacPO",["_FN",size+dir1,["x"]],["_FN",size+dir2,["x"]]]]

def part(size1,size2,dir1,dir2):
    return ["_F",["x"],["_BFN","P",["_FN",size1+dir1,["x"]],["_FN",size2+dir2,["x"]]]]

def inc(dir1,size):
    return ["_F",["x"],["_BFN","TangRayCont",["_FN","Ray"+dir1,["x"]],["_FN",size+dir1,["x"]]]]

#Saying x is East of y means the sector could be any size
def Underspecified(H):
    HL = H.Labels
    Claims = []
    Claims.append(Claim(["--Underspecified--"]))
    for l in HL:
        cl = ["_IFF",["_BFN","Adjacent"+l,["x"],["y"]],["_OR"]]
        if(len(l)<3):
           cl[2].append(po(Sizes[2],l))
           cl[2].append(po(Sizes[4],l))
        if(len(l)<=3):
            cl[2].append(po(Sizes[8],l))
        if(len(l)==4):
            cl[2].append(po(Sizes[16],l))
        Claims.append(Claim(cl))
    return Claims

#def BidirectionalCircle(H1,H2,offset=0): Not updated to new format!
#    H1L = H1.Labels
#    H2L = H2.Labels
#    if(offset is not 0):
#        H2L = H2.Labels[-offset:]+H2.Labels[:len(H2.Labels)-offset]
#    Size1 = Sizes[len(H1L)]
#    Size2 = Sizes[len(H2L)]
#    print "--Bidirectional--"
#    for i in range(len(H1L)):
#        outStr = po(Size1,H1L[i])+" <--> "
#        outStr += po(Size2,H2L[i*2])+" ^ "+po(Size2,H2L[((i*2)+1)])
#        print outStr

#def SingleDirectional(H1): Not updated to new format!
#    Size1 = Sizes[len(H1.Labels)]
#    Size2 = Sizes[len(H1.Labels)*2]
#    print "--Single Direction--"
#    for l in H1.Labels:
#        outStr = po(Size1,l)+" --> "+po(Size2,l)
#        print outStr

#Lists all of the Part relations where two sectors exhaustively form a third
### NE-4 and NW-4 together cover 100% of N-2
def ExhaustiveParts(H1,H2,offset=0):
    H1L = H1.Labels
    H2L = H2.Labels
    if(offset is not 0):
        H2L = H2.Labels[-offset:]+H2.Labels[:len(H2.Labels)-offset]
    Size1 = Sizes[len(H1L)]
    Size2 = Sizes[len(H2L)]
    Claims = []
    Claims.append(Claim(["--Exhaustive Parts--"]))
    for i in range(len(H1L)):
        Claims.append(Claim(part(Size2,Size1,H2L[i*2],H1L[i])))
        Claims.append(Claim(part(Size2,Size1,H2L[((i*2)+1)],H1L[i])))
    return Claims

#Lists where a sector is part of a larger one with the same label
### N-4 is part of N-2
def ContainedParts(H1):
    Size1 = Sizes[len(H1.Labels)]
    Size2 = Sizes[len(H1.Labels)*2]
    Claims = []
    Claims.append(Claim(["--Contained Parts--"]))
    for l in H1.Labels:
        Claims.append(Claim(part(Size2,Size1,l,l)))
    return Claims

#Establishes relations between sectors and their bounding rays
### N-2 is bound by RayW and RayE
def BContRays(H1,H2,offset=0):
    H1L = H1.Labels
    H2L = H2.Labels
    if(offset is not 0):
        H2L = H2.Labels[-offset:]+H2.Labels[:len(H2.Labels)-offset]
    Size = Sizes[len(H1L)]
    Claims = []
    Claims.append(Claim(["--BCont Rays--"]))
    for i in range(-1,len(H1L)-1):
        Claims.append(Claim(bc(H2L[i],H1L[i],Size)))
        Claims.append(Claim(bc(H2L[i],H1L[i+1],Size)))
    return Claims

#Rays that share an enpoint with the bounding rays of a sector but are contained
#   within that sector
### RayN is incidental to N-4
def IncRays(H):
    HL = H.Labels
    Size = Sizes[len(HL)]
    Claims = []
    Claims.append(Claim(["--Incidental Ray Containment--"]))
    for l in HL:
        Claims.append(Claim(inc(l,Size)))
    return Claims

#Used when the rays are not named so a relation cannot be established
##### this will be removed with the addition of 4-letter sixteenths #####
def ContactOnly(H):
    HL = H.Labels
    Claims = []
    Claims.append(Claim(["--Superficial Contact--"]))
    for i in range(len(HL)):
        Claims.append(Claim(sc(HL[i-1],HL[i])))
    return Claims

#Specifies that two sectors do not overlap
### N-2 does not overlap S-2
def NotOverlap(H):
    HL = H.Labels
    Size = Sizes[len(HL)]
    Claims = []
    Claims.append(Claim(["--Region Non-Overlap--"]))
    if(len(HL)==2):
        Claims.append(Claim(rd(HL[0],HL[1],Size)))
    else:
        for i in range(len(HL)):
            Claims.append(Claim(rd(HL[i-1],HL[i],Size)))
    return Claims

#Creates a subset of claims which all mention a specific hierarchy
def RoughSubsetByH(claims,hierarchy):
    HL = hierarchy.Labels
    outSet = []
    Size = Sizes[len(HL)]
    fullLabels = []
    for l in HL:
        fullLabels.append(Size+l)
    for c in claims:
        for l in fullLabels:
            if(c.usesLabel(l)):
               outSet.append(c)
    return outSet

#Writes a set of claims in either standard notation or CL. Can optionally
#   be output to a file
def WriteClaims(claims,parseType,fileName=None):
    if(parseType=="CL"):
        parseType=0
    elif(parseType==0):#excludes this from the 'else'
        parseType=0
    else:
        parseType="plain"
    if(fileName==None):
        for c in claims:
            print c.parse(parseType)
    else:
        f = open(fileName,"w")
        for c in claims:
            f.write(c.parse(parseType)+"\n")

#Writes all claims in CL. Additionally writes some CL-related syntax needed
#   for proper file management.
def WriteCLFile(claims,hierNames,bridge=False):
    name = "Base_"+hierNames[0]+".clif"
    if(bridge):
        name="Bridge_"+hierNames[0]+"_"+hierNames[1]+".clif"
    f = open(name,"w")
    f.write("(cl-text "+name+"\n\n")
    if(bridge):
        f.write("(cl-imports Base_"+hierNames[0]+".clif)\n\n")
        f.write("(cl-imports Base_"+hierNames[1]+".clif)\n\n")
    for c in claims:
        f.write(c.parse(0)+"\n\n")
    f.write(")")

#Takes two sets of claims and makes a 'venn diagram' of them, where the return
#   value is a 3 part list consisting of the unique claims of set 1, the unique
#   claims of set 2, and the shared claims, in that order
def VennClaims(claims1,claims2,parseType='plain'):
    bridge = []
    outC1 = claims1[:]
    outC2 = claims2[:]
    for c1 in claims1:
        if(c1 in claims2):
            bridge.append(c1)
    for cb in bridge:
        outC1.remove(cb)
        outC2.remove(cb)
    return [outC1,outC2,bridge]

#Gets the 'VennClaims' for every hierarchy with every other hierarchy
def FullVenn(claims,hierarchies,parseType="plain",writeCL=False):
    roughSubsets = []
    singleSubsets = []
    bridges = []
    for h in hierarchies:
        c = RoughSubsetByH(claims,h)
        roughSubsets.append(c[:])
        singleSubsets.append(c[:])
        bridges.append([])
    for i in range(len(roughSubsets)):
        for j in range(i+1,len(roughSubsets)):
            v = VennClaims(roughSubsets[i],roughSubsets[j])
            for c in v[2]:
                ind1 = listIndex(singleSubsets[i],c)
                if(ind1>-1):
                    del singleSubsets[i][ind1]
                ind2 = listIndex(singleSubsets[j],c)
                if(ind2>-1):
                    del singleSubsets[j][ind2]
            bridges[i].append(v[2])
    for i in range(len(roughSubsets)):
        print "-----Hierarchy #"+str(i)+"-----"
        if(writeCL):
            WriteCLFile(singleSubsets[i],[str(i)])
        else:
            for c in singleSubsets[i]:
                print c.parse("plain")
        for j in range(len(bridges[i])):
            print "--Bridge ("+str(i)+","+str(j+i+1)+")--"
            if(writeCL and len(bridges[i][j])>0):
                WriteCLFile(bridges[i][j],[str(i),str(j+i+1)],True)
            else:
                for c in bridges[i][j]:
                    print c.parse(parseType)

##TangentialRayContainment: If a ray has any overlap with a region's border,
##                          it is the ray's endpoint
TRC = Claim(["_IF",["_BFN","TangRayCont",["x"],["y"]],
             ["_AND",["_FN","Ray",["x"]],
                     ["_FN","ArealRegion",["y"]],
                     ["_BFN","Inc",["x"],["y"]],
                     ["_F",["z"],
                           ["_IF",["_AND",["_BFN","Inc",["z"],["x"]],
                                          ["_BFN","BCont",["z"],["y"]]],
                                  ["_BFN","Endpoint",["z"],["x"]]]]]])
AllClaims = [TRC]
AllClaims += Underspecified(SixteenthA)
AllClaims += Underspecified(SixteenthB)
AllClaims += ExhaustiveParts(HalfA,QuarterA)
AllClaims += ExhaustiveParts(HalfB,QuarterA,1)
AllClaims += ExhaustiveParts(HalfC,QuarterB)
AllClaims += ExhaustiveParts(HalfD,QuarterB,3)
AllClaims += ExhaustiveParts(QuarterA,EighthA)
AllClaims += ExhaustiveParts(QuarterB,EighthA,1)
AllClaims += ExhaustiveParts(EighthA,SixteenthB)
AllClaims += ExhaustiveParts(EighthB,SixteenthB,1)
AllClaims += ContainedParts(HalfA)
AllClaims += ContainedParts(HalfB)
AllClaims += ContainedParts(HalfC)
AllClaims += ContainedParts(HalfD)
AllClaims += ContainedParts(QuarterA)
AllClaims += ContainedParts(QuarterB)
AllClaims += ContainedParts(EighthB)
AllClaims += BContRays(HalfA,HalfB)
AllClaims += BContRays(HalfB,HalfA)
AllClaims += BContRays(HalfC,HalfD)
AllClaims += BContRays(HalfD,HalfC)
AllClaims += BContRays(QuarterA,QuarterB,3)
AllClaims += BContRays(QuarterB,QuarterA)
AllClaims += BContRays(EighthA,EighthB,7)
AllClaims += BContRays(EighthB,EighthA)
AllClaims += BContRays(SixteenthA,SixteenthB)
AllClaims += BContRays(SixteenthB,SixteenthA,15)
###AllClaims += ContactOnly(SixteenthA)#Because we don't have rays that granular
for x in AllHierarchies:
    AllClaims += NotOverlap(x)
    AllClaims += IncRays(x)

if __name__ == '__main__':
    #FullVenn(AllClaims,AllHierarchies)
    #FullVenn(AllClaims,AllHierarchies)

    WriteClaims(AllClaims,"plain")
    """
    HalfASub = RoughSubsetByH(AllClaims,HalfA)
    HalfBSub = RoughSubsetByH(AllClaims,HalfB)
    HalfCSub = RoughSubsetByH(AllClaims,HalfC)
    HalfDSub = RoughSubsetByH(AllClaims,HalfD)
    QuarterASub = RoughSubsetByH(AllClaims,QuarterA)
    QuarterBSub = RoughSubsetByH(AllClaims,QuarterB)
    EighthASub = RoughSubsetByH(AllClaims,EighthA)
    EighthBSub = RoughSubsetByH(AllClaims,EighthB)
    SixteenthASub = RoughSubsetByH(AllClaims,SixteenthA)
    """

    #VennClaims(HalfASub,QuarterASub)

    #WriteClaims(HalfASub,"plain")
    #WriteClaims(HalfASub,"CL")
    #WriteClaims(HalfASub,"plain","plain.txt")
    #WriteClaims(HalfASub,"CL","CL.txt")
