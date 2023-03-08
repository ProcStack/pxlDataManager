from os import listdir, stat
from os.path import isfile, isdir, join, realpath
import re
import datetime
import math

# Update this as need be
repoName="pxlDataManager"
statProjectTitle="pxlDataManager Scripting Stats"

basePath=re.split( r'[\\|/]', realpath(__file__) )
basePath="/".join( basePath[ 0:-2 ] )

#Stats file output
statPath=[ basePath+"/stats/LineCounterOutput/pdm_ScriptingStats_", ".txt" ]

# Recursive Directories
dirs=[ basePath+'/scripts/' ]#, basePath+'/_Utils/' ]
bypassList=['.git']
bypassFolderIncludeList=['__']
bypassFileExtension=['pyc']

        
#The manual added files
filePaths=[
        basePath+'/README.md',
        basePath+'/pxlDataManager.py'
    ]

def filterBypassFiles( curFile ):
    for bypass in bypassList:
        if bypass in curFile:
            return False
    curExt = curFile.split(".")[-1]
    return curExt not in bypassFileExtension

def filterBypassFolders( curFolder ):
    for bypassInclude in bypassFolderIncludeList:
        if bypassInclude in curFolder:
            return False
    return True
            

# Recursively move through directories and gather all files
while len(dirs)>0:
    curDir=dirs.pop()
    
    pathSplit= list(filter(None, list( re.split( r'[/|\\]', curDir) )))
    coreCount=0
            
    foundFiles = [f for f in listdir(curDir) if isfile(join(curDir, f))]
    foundFiles = list(filter( filterBypassFiles, foundFiles ))
    foundFiles = list(map( lambda x: join(curDir, x), foundFiles )) 
    
    filePaths += foundFiles
    
    foundDirs = [f for f in listdir(curDir) if isdir(join(curDir, f))] 
    foundDirs = list(filter( filterBypassFolders, foundDirs ))
    foundDirs = list(map( lambda x: join(curDir, x), foundDirs )) 
    
    dirs += foundDirs



# Extention List
#extFoundList=list(set([ x.split(".")[-1].upper() for x in filePaths]))
#extFoundList.sort()

extFullList=[ x.split(".")[-1].upper() for x in filePaths]
extFoundList=list(set(extFullList))
extFoundList.sort()
extFoundList = list(map(lambda x: x+" : "+str(extFullList.count(x))+" Files" ,extFoundList))

# Sort by name, swap delimiter just to be safe
filePathSorted=[ "/".join( re.split(r'[\\|/]',x) ) for x in filePaths  ]
filePathSorted.sort()



def bytesToHuman(bytes, pad=False):
    k=1024
    cur=bytes
    count=0
    while cur>=k:
        cur=cur/k
        count+=1
    disp= " "+[(" " if pad else "")+"B","KB","MB","GB","TB","PB"][count]
    hr=str(cur)
    if count==0 :
        hr= ( hr.rjust( 8, " " ) if pad else hr )+disp
    else:
        hr= hr.split(".") if "." in hr else [hr,'000']
        unit=len(hr[0])
        dec=4-unit
        if pad:
            hr[0]=hr[0].rjust(4, ' ')
            hr[1]=hr[1].ljust(dec,"0")[0:dec]
        else:
            hr[1]=hr[1][0:dec]
        hr=".".join(hr)+disp
    return hr;

# Gather total file size in human readable format
totalFileSize=0;
for f in filePathSorted:
    totalFileSize+=stat(f).st_size
totalFileSize=bytesToHuman(totalFileSize)


def lineCount(fpaths, spacer):



    textOnlyExtensions = ["txt", "md"]
    isWebScriptOnlyExtensions = ["html", "js", "ts"]
    isPythonOnlyExtensions = ["py"]
    
    webCommentDelimiter = r'\/\/.*'
    webCommentBlock = r'\/\*[\s\S]*?\*\/'
    webAllComments = r'(\/\*[\s\S]*?\*\/)|(\/\/.*)'
    
    pythonCommentDelimiter = r'#.*'
    pythonVariableCommentBlock = r'(.*=.(\'\'\'|\s\"\"\")[\s\S]*?(\'\'\'|\"\"\"))'
    pythonCommentBlock = r'(\'''|\""")[\s\S]*?(\'''|\""")'
    #pythonAllComments = r'((\'''|\""")[\s\S]*?(\'''|\"""))|(#.*)'
    pythonAllComments = r'((\'\'\'|\"\"\")[\s\S]*?(\'\'\'|\"\"\"))|(#.*)'


    totalCount=0
    totalCodeLineCount=0
    totalCommentCount=0
    totalDocumentationCount=0
    
    fileCount=0
    zfillCount=len(str(len(fpaths)))
    
    finalPrint=""
    while len(fpaths)>0:
        curfile=fpaths.pop()
            
        commentBlockOpen=False
        devBlockOpen=False
        modBlockOpen=False
        
        

        curExt=curfile.split(".")[-1].lower()
        isTextOnly= curExt in textOnlyExtensions
        isWebScriptOnly= curExt in isWebScriptOnlyExtensions
        isPythonOnly= curExt in isPythonOnlyExtensions
        
        curFileCommentDelimiter = ""
        curFileCommentBlock = ""
        curFileAllComments = ""

        if isWebScriptOnly:
            curFileCommentDelimiter = webCommentDelimiter
            curFileCommentBlock = webCommentBlock
            curFileAllComments = webAllComments
        elif isPythonOnly:
            curFileCommentDelimiter = pythonCommentDelimiter
            curFileCommentBlock = pythonCommentBlock
            curFileAllComments = pythonAllComments
        
        
        
        with open(curfile, encoding="utf-8") as f:
            fileCount+=1
            curTotalLineCount=0
            curCodeCount=0
            curComments=0
            curWhiteSpace=0
            checkEmptyCommentLine=False
            
            fileContents = f.read()
            curTotalLineCount = len(fileContents.split("\n"))
            
            if isTextOnly :
                curDocLines = re.sub( r'((<br>)|#|\"|\'|\t| |-)',"",fileContents)
                curDocLines = curDocLines.split("\n")
                curDocLines = list(filter( lambda x: len(x)>0, curDocLines))
                curDocCount = len(curDocLines)
                
                fname="/".join( ['']+re.split(r'[\\|/]',curfile)[4::] )
                finalPrint+="\n  "+str(fileCount).zfill(zfillCount)+"; Documentation - "
                finalPrint+="\n    "+ fname
                finalPrint+="\n     - File Size - "+bytesToHuman( stat(curfile).st_size )
                finalPrint+="\n     - Total Line Count - "+str(curTotalLineCount)
                finalPrint+="\n     - Information Line Count - "+str(curDocCount)
                finalPrint+="\n\n"
                
                totalCount+=curTotalLineCount
                totalDocumentationCount+=curDocCount
            else:
                if isPythonOnly:
                    commendBlockVariables = re.findall( pythonVariableCommentBlock, fileContents )
            
                # Remove all comments & comment blocks
                fileCodeOnly = re.sub( curFileAllComments, "", fileContents )
                if isPythonOnly and len(commendBlockVariables)>0:
                    commendBlockVariables = list(map( lambda x: "".join(list(x)), commendBlockVariables))
                    fileCodeOnly += "\n" + "\n".join(commendBlockVariables)
                # Clear empty lines; spaces, tabs, till the next return
                fileCodeOnly = re.sub( r'( )+(?![\S\w\d])\n', "", fileCodeOnly )
                fileCodeArray = fileCodeOnly.split("\n")
                fileCodeArray = list(filter(None,fileCodeArray))
                fileCodeArray = list(filter( lambda x: len(re.sub(" ","",x))>0 ,fileCodeArray ))
                curCodeCount += len(fileCodeArray)
                
                
                # Extract comments only, blocks & single line comments
                fileCommentsOnly = re.findall( curFileAllComments, fileContents )
                fileCommentsOnly = list(map( lambda x: list(filter(lambda g: g not in [None,'','"',"'","#"],x)), fileCommentsOnly ))
                fileCommentsOnly = list(filter(None,fileCommentsOnly))
                #fileCommentsOnly = ("\n".join(fileCommentsOnly))#.split("\n")
                for c in fileCommentsOnly:
                    curline=[]
                    for s in c:
                        curSub = s.split('\n')
                        for v in curSub:
                            curv = re.sub(r'[ \n\'\"#]','',v)
                            if len(curv)>0:
                                curline.append(curv)
                    curComments += len(curline)
                    #curline = list( filter( lambda x: len(re.sub(r'[ #\'\"]','',x))>0, c))
                    #print(curline)
                
                # Append per-file stats to file data
                fname="/".join( ['']+re.split(r'[\\|/]',curfile)[4::] )
                finalPrint+="\n  "+str(fileCount).zfill(zfillCount)+"; Code - "
                finalPrint+="\n    "+ fname
                finalPrint+="\n     - File Size - "+bytesToHuman( stat(curfile).st_size )
                finalPrint+="\n     - Total Line Count - "+str(curTotalLineCount)
                finalPrint+="\n     - Code Line Count - "+str(curCodeCount)
                finalPrint+="\n     - Commented Line Count - "+str(curComments)
                finalPrint+="\n\n"
            
                totalCount+=curTotalLineCount
                totalCodeLineCount+=curCodeCount
                totalCommentCount+=curComments
            
    
    spacer="\n\n"+spacer+"\n\n"
    tab="    "
    dtab=tab+tab
    shift=tab+"         "
    # Stat File header
    header=""
    header+=tab+"Stats Overview - \n\n"
    header+=dtab+"Files Found - \n"+shift+str(fileCount)+"\n"
    header+=dtab+"File Types Checked - \n"+shift+(("\n"+shift).join( extFoundList ))+"\n"
    header+=dtab+"Total Size Of Files - \n"+shift+str(totalFileSize)+"\n"
    header+=dtab+"Total File Line Count - \n"+shift+str(totalCount)+"\n\n"
    header+=dtab+"-- Below are Empty Lines Removed -- \n    -- Whitespace, Quotes, and # Only Lines --\n\n"
    header+=dtab+"Code Line Count - \n"+shift+str(totalCodeLineCount)+"\n"
    header+=dtab+"Comments In Code Line Count - \n"+shift+str( totalCommentCount)+"\n"
    header+=dtab+"Documentation File Info Line Count  - \n"+shift+str( totalDocumentationCount)
    header+=spacer
    print(header)
    header+=finalPrint
    header+=spacer
    return header



# Gather Month Day, Year
date=datetime.datetime.now()
monthdayyear=" "+date.strftime("%B")+" "+str(date.day)+", "+str(date.year)+" "
spacer=" -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- "
padHeader=3
padDate=6
statProjectTitle=(" " if statProjectTitle[0] != " " else "") + statProjectTitle+(" " if statProjectTitle[-1] != " " else "")
padHeaderEnd=len(statProjectTitle)+padHeader
header="\n"+spacer[0:padHeader]+statProjectTitle+spacer[ padHeaderEnd:: ]
padEnd=len(monthdayyear)+padDate
# Set spacer design
header+="\n"+spacer[0:padDate]+monthdayyear+spacer[ padEnd:: ]+"\n"

print(header)



fileData = lineCount(filePathSorted, spacer)
fileData=header+fileData

date=datetime.datetime.now()
yearmonthday=str(date.year)+"-"+str(date.month)+"-"+str(date.day)
fileOut=yearmonthday.join( statPath )

f = open(fileOut, "w")
f.write(fileData)
f.close()

