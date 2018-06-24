#Compares the output from our analysis and a DRM analysis and outputs a LaTeX
#    longtable which adds highlighting based on how closely the results align
#Expects the files to be formatted in a specific way
##fn1 - name of a text file containing output from DRM analysis
##fn2 - name of a text file containing output from our analysis
def WriteTable(fn1="ForTex_DRM.txt",fn2="ForTex_Ours.txt"):
    fDRM = open(fn1,'r')
    fCAR = open(fn2,'r')

    nextline = fCAR.readline()
    fDRM.readline()

    print "\\begin{longtable}[c]{| c | c | c | c |}"
    print "\hline"
    print "\\textbf{Reference} & \\textbf{Target} & \\textbf{DRM} & \\textbf{Ours} \\\\ \hline"

    while(nextline):
        fromObj = nextline.split(":")[1][1:-1]
        nextline = fCAR.readline()
        tgtSet = []
        tgtDRM = {}
        tgtCAR = {}
        nextline = fCAR.readline()
        while((nextline is not None) and (len(nextline)>2)):
            tgt = nextline.split(" ")[0]
            lab = nextline.split("'")[1]
            tgtSet.append(tgt)
            tgtCAR[tgt] = lab
            nextline = fCAR.readline()
        nextline = fDRM.readline()
        while((len(nextline)>2) and ("Examining" not in nextline)):
            tgt = nextline.split(" ")[4][:-2]
            nextline = fDRM.readline()
            labs = nextline.split(" ")[4][:-1]
            labsList = labs.split(",")
            tgtDRM[tgt] = labsList
            nextline = fDRM.readline()
        if(nextline is not None):
            nextline = fCAR.readline()
        if("Unknown" in tgtSet):
            tgtSet.remove("Unknown")
        for tgt in tgtSet:
            carDir = tgtCAR[tgt].split("-")[0]
            numRep = tgtCAR[tgt]
            print fromObj,"&",tgt,"&",
            drmRow = ""
            if(carDir in tgtDRM[tgt]):
                for i in range(len(tgtDRM[tgt])):
                    if(tgtDRM[tgt][i]==carDir):
                        drmRow += "\\textcolor{Green}{"+tgtDRM[tgt][i]+"},"
                    else:
                        drmRow += tgtDRM[tgt][i]+","
                drmRow = drmRow[:-1]
                print drmRow,"&","\\textcolor{Green}{"+numRep+"} \\\\ \hline"
            elif(len(carDir)==3 and
                 ((carDir[0] in tgtDRM[tgt]) or (carDir[1:] in tgtDRM[tgt]))):
                for i in range(len(tgtDRM[tgt])):
                    if(tgtDRM[tgt][i]==carDir[0] or tgtDRM[tgt][i]==carDir[1:]):
                        drmRow += "\\textcolor{YellowOrange}{"+tgtDRM[tgt][i]+"},"
                    else:
                        drmRow += tgtDRM[tgt][i]+","
                drmRow = drmRow[:-1]
                print drmRow,"&","\\textcolor{YellowOrange}{"+numRep+"} \\\\ \hline"
            else:
                for i in range(len(tgtDRM[tgt])):
                    drmRow += tgtDRM[tgt][i]+","
                drmRow = drmRow[:-1]
                print drmRow,"&","\\textcolor{red}{"+numRep+"} \\\\ \hline"

    print "\caption{Comparison of direction-relation matrix to our method}"
    print "\end{longtable}"

    fDRM.close()
    fCAR.close()

if __name__ == '__main__':
    WriteTable(fn2="ForTex_Ours2.txt")
