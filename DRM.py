import arcpy,os,sys,math,collections

#A class for the direction-relation matrix
#It is very much tuned for its usage in this program. (i.e. not general at all)
#This was easier and less ambiguous to read than doing this inline
class DRMatrix:
    def __init__(self,boolAryArg):
        self.boolAry = boolAryArg
        tr = [3,2,1,4,8,0,5,6,7]
        dr = ["E","NE","N","NW","W","SW","S","SE","C"]
        for i in range(9):
            if(not self.boolAry[i]):
                dr[tr[i]]="x"
        self.listRep = ""
        for i in range(8):
            if(dr[i] is not "x"):
                self.listRep += dr[i]+","
        self.listRep = self.listRep[:-1]

    #Returns a visual representation of the matrix
    def visRep(self):
        outLines = ["-------------"]
        nextLine = ""
        for i in range(9):
            if(not self.boolAry[i]):
                nextLine += "| F "
            else:
                nextLine += "| T "
            if(i%3==2):
                nextLine += "|"
                outLines.append(nextLine)
                nextLine = ""
                outLines.append("-------------")
        return outLines
        
    #Prints the visual representation of the matrix.
    #Pad allows it to stay inline
    def printMatrix(self,pad=""):
        for l in self.visRep():
            print pad+l

    #Returns the list of sectors in counterclockwise order, excluding the center
    def printList(self):
        return self.listRep
                
        
#Calculates the direction-relation matrix for each of a collection of polygons
##inpTable - filepath to table of polygons
##inpColName - names the column containing the polygon names
def boundingBoxes(inpTable,inpColName,fn=None):
    polyFN = os.path.join(homeFolder,inpTable)
    polyKeys = ["Shape@","Shape@XY",inpColName]
    poly_crs_a = arcpy.da.SearchCursor(polyFN,polyKeys)
    ltw = None
    fOut = None
    if(fn):
        fOut = open(fn,'w')
    for poly_a in poly_crs_a:
        if(fOut):
            if(ltw):
                fOut.write(ltw+"\n")
                ltw = None
            fOut.write("Examining from "+str(poly_a[2])+"\n")
        else:
            print "Examining from",poly_a[2]
        aExt = poly_a[0].extent
        poly_crs_b = arcpy.da.SearchCursor(polyFN,polyKeys)
        for poly_b in poly_crs_b:
            if((poly_a[2] != poly_b[2]) and
               (not poly_a[0].disjoint(poly_b[0]))):
                if(fOut):
                    if(ltw):
                        fOut.write(ltw+"\n")
                    fOut.write("  Intersection with "+str(poly_b[2])+":\n")
                else:
                    print "  Intersection with",poly_b[2]+":"
                tPoly = poly_a[0].union(poly_b[0])
                tExt = tPoly.extent
                PTS = []
                for ypt in [tExt.YMax,aExt.YMax,aExt.YMin,tExt.YMin]:
                    for xpt in [tExt.XMin,aExt.XMin,aExt.XMax,tExt.XMax]:
                        PTS.append(arcpy.Point(xpt,ypt))
                BXS = []
                for i in range(9):
                    tx = i%3
                    ty = i/3
                    TL = PTS[tx+(4*ty)]
                    TR = PTS[tx+1+(4*ty)]
                    BR = PTS[tx+1+(4*(ty+1))]
                    BL = PTS[tx+(4*(ty+1))]
                    BXS.append(arcpy.Polygon(arcpy.Array([TL,TR,BR,BL,TL])))
                tf = []
                for i in range(9):
                    tf.append(not BXS[i].disjoint(poly_b[0]))
                drm = DRMatrix(tf)
                if(fOut):
                    ltw = "   "+drm.printList()
                else:
                    print "   ",drm.printList()
    if(fn):
        fOut.write(ltw)
        fOut.close()

#This should be set to the filepath of your geodatabase
homeFolder = 'C:\Users\Greg\ArcGIS\Test.gdb'

if __name__ == '__main__':
    print "Starting!"
    boundingBoxes("Maine\Counties_Trimmed","COUNTY")
    print "...Done..."
