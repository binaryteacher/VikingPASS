import cv2
import numpy as np
import tkinter as tk
import os
import datetime as dt

'''
  VikingPASS (Portable Answer Sheet Scanner)
  
  Scans a proprietary multiple choice answer sheet (pdf and png are provided)
  from the camera and determines which bubbles are selected for each of a possible 50 questions.
  It compares the selected answers with a user input text text key.
  It shows an image of the scanned test and displays the score and the 
  number of questions left unanswered (i.e. not read by the scanner).
  This image is saved for the teacher in a directory named with the current date and time.

  Copyright (C) 2023 - 
  Author: David Ruth - binaryteacher - 
  
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ VikingPASS_beta2 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

#utility class for a Rectangle .. ( x-coordinate,y-coordinate,width,height)
class Rect:
  def __init__(self,x,y,w,h):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.x2 = x + w
    self.y2 = y + h
  def __str__(self):
    return "("+str(self.x)+","+str(self.y)+"),("+ \
      str(self.x2)+","+str(self.y2)+")"+" ~ "+ \
      str(self.w)+"x"+str(self.h)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

# some useful constants
red,green,blue,cyan,magenta,yellow,black,white,gray = \
(0,0,255),(0,255,0),(255,0,0),(255,255,0),(255,0,255),(0,255,255),(0,0,0),(255,255,255),(128,128,128)#colors in BGR
center = (320,240) #image resolution is 640x480

#global variables for main program
testOutline = Rect(145,200,350,270)#260x340 ~ 8.5x11 standard paper
topGuideSqr = Rect(445,230,20,20)
botGuideSqr = Rect(175,420,20,20)
topLeft,topRight,botLeft,botRight = Rect(0,0,0,0),Rect(0,0,0,0),Rect(0,0,0,0),Rect(0,0,0,0)
midLeft,mid20,mid40,midRight = Rect(0,0,0,0),Rect(0,0,0,0),Rect(0,0,0,0),Rect(0,0,0,0)

studentFrame = np.zeros((480,640,3), dtype=np.uint8)
teacherFrame = np.zeros((480,640,3), dtype=np.uint8)
logoPic150x150 = np.zeros((150,150,3), dtype=np.uint8)
logoPic75x75 = np.zeros((75,75,3), dtype=np.uint8)

threshold,threshOffset = 140,0
frameCnt,inRangeCnt,showScoreCnt,showThreshCnt = 0,0,0,0
faceInRange,faceInRangeOn,testInRange,validScan, helpAnimation = False,False,False,False,False

answerFreq = [[0]*5]*51 #answer frequency for item analysis ..leave first row blank
answerList = []
answerStr = ""
answerKey = ['~','A','C','D','C','AB','A','B','B','C','C']
numQuestions = 10
totalScore,numUnanswered = 0,0
directory = ''
imageNum = 1

windowTitle = 'VikingPASS'

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def initSaveDirectory():
  global directory
  curDate = dt.date.today().strftime('%B %d, %Y')
  curTime = dt.datetime.now().strftime('%I_%M_%p')
  directory = "Test on "+str(curDate) + ' at ' + str(curTime)
  #print(directory)
  if not os.path.isdir(directory):
    os.mkdir(directory)
 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def readAnswerKey():
  global answerKey, numQuestions
  root = tk.Tk()
  root.title("Input Answer Key")
  root.geometry("640x480")
  root.config(bg="#CBC3E3")
  textArea = tk.Text(root, height = 15, width = 10)
  textArea.config(font =("Courier"))
  lbl = tk.Label(root, text="Paste answer key from your Spreadsheet Column",font="Courier",bg="#CBC3E3")
  lbl2 = tk.Label(root, text = "",font="Courier",bg="#CBC3E3")
  lbl3 = tk.Label(root, text = "",font="Courier",bg="#CBC3E3")
  try:
    img = tk.PhotoImage(file = "logo150x150.png")
    lblImg1 = tk.Label(root, image=img, borderwidth=0)
    lblImg2 = tk.Label(root, image=img, borderwidth=0)
  except:
    print('could not load image')
    lblImg1 = tk.Label(root, text = "", bg="#CBC3E3")
    lblImg2 = tk.Label(root, text = "", bg="#CBC3E3")
  
  btn1 = tk.Button(root, text = "Submit", font="Courier", bg="#CBC3E3", \
    command = lambda:[tempStr := textArea.get(1.0,"end"), \
    f := open("tempKey.txt", "w"), f.write(tempStr), f.close() , root.destroy()])
  
  lblImg1.place(x = 50, y = 200)
  lblImg2.place(x = 640-160-50, y = 200)
  
  lbl.pack()
  lbl2.pack()
  textArea.pack()
  lbl3.pack()
  btn1.pack()
  textArea.focus_set()
 
  tk.mainloop()
  
  f = open("tempKey.txt", "r")
  answerKey = f.readlines()
  answerKey = [line.rstrip().upper() for line in answerKey]
  while('' in answerKey):
    answerKey.remove('')
  numQuestions = len(answerKey)
  answerKey.insert(0, '~')
  #print(answerKey)
  tempStr = "0,"
  
  for ch in answerKey:
    tempStr += ch + ',' 
  answerList.append(tempStr)
  
  f.close()
  #print(answerList)


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def isFaceInRange(frame):
  inRange = False
  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  faces = clf.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30, 30),
    flags=cv2.CASCADE_SCALE_IMAGE
  )
  buf = 80
  for (x, y, width, height) in faces:
    if ( x > 230-buf and x < 230+buf and y > -40 and y < 40+buf):
      inRange = True
      cv2.ellipse(frame, (320,100), (70,90), 0, 0, 360, cyan, 3)
  return inRange

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def isTestInRange(frame,testBin,testBinInv):

  topInRange, botInRange, upsideDown = False,False,False
  #testOutline 270 rows 350 cols
    
  topSqrNumBlack,topSqrLeftNumWhite,topSqrBelowNumWhite=0,0,0
  botSqrNumBlack,botSqrLeftNumWhite,botSqrBelowNumWhite=0,0,0
  logoSqrNumBlack = 0
  
  topSqrNumBlack = len(np.flatnonzero(testBinInv[30:50,30:50]))
  topSqrLeftNumWhite = len(np.flatnonzero(testBin[20:60,20:30]))
  topSqrBelowNumWhite = len(np.flatnonzero(testBin[50:60,20:60]))
  
  botSqrNumBlack = len(np.flatnonzero(testBinInv[220:240,300:320]))
  botSqrRightNumWhite = len(np.flatnonzero(testBin[210:250,320:330]))
  botSqrAboveNumWhite = len(np.flatnonzero(testBin[210:220,290:330]))
  #cv2.putText(frame, 'numZero:'+str(topSqrNumBlack),(100,100) , 0, 1, white, 2, cv2.LINE_AA)
  
  nilesNorthLogo = len(np.flatnonzero(testBinInv[200:250, 25:55]))
  
  sqrCntMin = 200
  if topSqrNumBlack>sqrCntMin + 20 and topSqrLeftNumWhite>sqrCntMin and topSqrBelowNumWhite>sqrCntMin:
    topInRange = True
  if botSqrNumBlack>sqrCntMin + 20 and botSqrRightNumWhite>sqrCntMin and botSqrAboveNumWhite>sqrCntMin:
    botInRange = True
  
  if topInRange:
    cv2.rectangle(frame,(topGuideSqr.x,topGuideSqr.y),(topGuideSqr.x2,topGuideSqr.y2),cyan,2)
  if botInRange:
    cv2.rectangle(frame,(botGuideSqr.x,botGuideSqr.y),(botGuideSqr.x2,botGuideSqr.y2),cyan,2)
  if topInRange and botInRange:
    cv2.rectangle(frame, (testOutline.x,testOutline.y), (testOutline.x2,testOutline.y2), cyan, 2)
  
  return topInRange and botInRange and nilesNorthLogo < 80

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def getFourGuideRectsTopBottom(frame,testBin,testBinInv):
  global topLeft,topRight,botLeft,botRight
  global studentFrame,teacherFrame
 
  # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  # ~~~ botLeft ~~~ botLeft ~~~ botLeft
  # ~~~ botLeft ~~~ botLeft ~~~ botLeft
  
  rowCntMin = 7
  row,rowMin = 265,220 #5 px from bottom
  col,colMax = 125,155
  while np.count_nonzero(testBinInv[row][col:colMax]) < rowCntMin and row > rowMin:
    row -= 1 
  if row == rowMin:
    print('ERROR!!! COULD NOT GET botLeft ANSWER GUIDE SQUARE')
    return False
  
  botLeft.y2 = row;
  indexes = np.nonzero(testBinInv[row-1][col:colMax])[0]
  botLeft.x = indexes[0] + col;
  botLeft.x2 = indexes[-1] + col;
  
  midCol = (indexes[0] + indexes[-1]) // 2  
  while testBinInv[row][midCol+col] != 0 and row > rowMin:
    row -= 1 
  if row == rowMin:
    print('ERROR!!! COULD NOT GET botLeft ANSWER GUIDE SQUARE')
    return False
  
  botLeft.y = row + 1;
  botLeft.w = botLeft.x2 - botLeft.x
  botLeft.h = botLeft.y2 - botLeft.y
    
  # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  # ~~~ botRight ~~~ botRight ~~~ botRight
  # ~~~ botRight ~~~ botRight ~~~ botRight
  
  row,rowMin = 265,220 #5 px from bottom
  col,colMax = 180,210
  while np.count_nonzero(testBinInv[row][col:colMax]) < rowCntMin and row > rowMin:
    row -= 1 
  if row == rowMin:
    print('ERROR!!! COULD NOT GET botRight ANSWER GUIDE SQUARE')
    return False
  
  botRight.y2 = row;
  indexes = np.nonzero(testBinInv[row-1][col:colMax])[0]
  botRight.x = indexes[0] + col;
  botRight.x2 = indexes[-1] + col;
  
  midCol = (indexes[0] + indexes[-1]) // 2
  while testBinInv[row][midCol+col] != 0 and row > rowMin:
    row -= 1
  
  if row == rowMin:
    print('ERROR!!! COULD NOT GET botRight ANSWER GUIDE SQUARE')
    return False
  
  botRight.y = row + 1;
  botRight.w = botRight.x2 - botRight.x
  botRight.h = botRight.y2 - botRight.y
 
  # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  # ~~~ topLeft ~~~ topLeft ~~~ topLeft
  # ~~~ topLeft ~~~ topLeft ~~~ topLeft

  row,rowMax = 15,55 #15 px from top
  col,colMax = 125,155
  while np.count_nonzero(testBinInv[row][col:colMax]) < rowCntMin and row < rowMax:
    row += 1 
  if row == rowMax:
    print('ERROR!!! COULD NOT GET topLeft ANSWER GUIDE SQUARE')
    return False
  
  topLeft.y = row;
  indexes = np.nonzero(testBinInv[row+1][col:colMax])[0]
  topLeft.x = indexes[0] + col;
  topLeft.x2 = indexes[-1] + col;
  
  midCol = (indexes[0] + indexes[-1]) // 2
  #print(indexes)
  #print('row before col loop',row)
  #print('midCol and testBinInv[row][midCol]',midCol,testBinInv[row][midCol])
  
  while testBinInv[row][midCol+col] != 0 and row < rowMax:
    row += 1
  if row == rowMax:
    print('ERROR!!! COULD NOT GET topLeft ANSWER GUIDE SQUARE')
    return False
  
  topLeft.y2 = row - 1;
  topLeft.w = topLeft.x2 - topLeft.x
  topLeft.h = topLeft.y2 - topLeft.y

  # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  # ~~~ topRight ~~~ topRight ~~~ topRight
  # ~~~ topRight ~~~ topRight ~~~ topRight
  
  row,rowMax = 15,55 #15 px from top
  col,colMax = 180,210
  while np.count_nonzero(testBinInv[row][col:colMax]) < rowCntMin and row < rowMax:
    row += 1 
  if row == rowMax:
    print('ERROR!!! COULD NOT GET topRight ANSWER GUIDE SQUARE')
    return False
  
  topRight.y = row;
  indexes = np.nonzero(testBinInv[row+1][col:colMax])[0]
  topRight.x = indexes[0] + col;
  topRight.x2 = indexes[-1] + col;
  
  midCol = (indexes[0] + indexes[-1]) // 2  
  while testBinInv[row][midCol+col] != 0 and row < rowMax:
    row += 1
  
  if row == rowMax:
    print('ERROR!!! COULD NOT GET topRight ANSWER GUIDE SQUARE')
    return False
  
  topRight.y2 = row - 1;
  topRight.w = topRight.x2 - topRight.x
  topRight.h = topRight.y2 - topRight.y 
  
  return True
 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
   
def getFourGuideRectsMiddle(frame,testBin,testBinInv):
  global midLeft,mid20,mid40,midRight
  global studentFrame,teacherFrame
  
  # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  # ~~~ midLeft ~~~ midLeft ~~~ midLeft
  # ~~~ midLeft ~~~ midLeft ~~~ midLeft
  
  rowCntMin = 7
  row,rowMax = 125,145 #approx middle
  col,colMax = 70,110

  
  while np.count_nonzero(testBinInv[row][col:colMax]) < rowCntMin and row < rowMax:
    row += 1 
  if row == rowMax:
    print('ERROR!!! COULD NOT GET midLeft ANSWER GUIDE SQUARE')
    return False
  
  midLeft.y = row;
  indexes = np.nonzero(testBinInv[row+1][col:colMax])[0]
  midLeft.x = indexes[0] + col;
  midLeft.x2 = indexes[-1] + col;
  
  midCol = (indexes[0] + indexes[-1]) // 2    
  while testBinInv[row][midCol+col] != 0 and row < rowMax:
    row += 1 
  if row == rowMax:
    print('ERROR!!! COULD NOT GET topLeft ANSWER GUIDE SQUARE')
    return False
  
  midLeft.y2 = row - 1;
  midLeft.w = midLeft.x2 - midLeft.x
  midLeft.h = midLeft.y2 - midLeft.y
  
  
  # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  # ~~~ midRight ~~~ midRight ~~~ midRight
  # ~~~ midRight ~~~ midRight ~~~ midRight
  
  row,rowMax = 125,145 #approx middle
  col,colMax = 230,270
  
  while np.count_nonzero(testBinInv[row][col:colMax]) < rowCntMin and row < rowMax:
    row += 1 
  if row == rowMax:
    print('ERROR!!! COULD NOT GET midRight ANSWER GUIDE SQUARE')
    return False
  
  midRight.y = row;
  indexes = np.nonzero(testBinInv[row+1][col:colMax])[0]
  midRight.x = indexes[0] + col;
  midRight.x2 = indexes[-1] + col;
  
  midCol = (indexes[0] + indexes[-1]) // 2    
  while testBinInv[row][midCol+col] != 0 and row < rowMax:
    row += 1 
  if row == rowMax:
    print('ERROR!!! COULD NOT GET midRight ANSWER GUIDE SQUARE')
    return False
  
  midRight.y2 = row - 1;
  midRight.w = midRight.x2 - midRight.x
  midRight.h = midRight.y2 - midRight.y
  
  # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  # ~~~ mid20 ~~~ mid20 ~~~ mid20
  # ~~~ mid40 ~~~ midR40 ~~~ mid40
  
  dx = (midRight.x - midLeft.x)/3.0
  dx2 = (midRight.x2 - midLeft.x2)/3.0
  mid20.x = int(midLeft.x + dx + 0.5)
  mid20.x2 = int(midLeft.x2 + dx2 + 0.5)
  mid40.x = int(midLeft.x + 2 * dx + 0.5)
  mid40.x2 = int(midLeft.x2 + 2 * dx2 + 0.5)
  
  slope = (midRight.y - midLeft.y) / (midRight.x - midLeft.x)
  mid20.y = int(midLeft.y + slope * dx + 0.5)
  mid20.y2 = int(midLeft.y2 + slope * dx + 0.5)
  mid40.y = int(midLeft.y + slope * 2 * dx + 0.5)
  mid40.y2 = int(midLeft.y2 + slope * 2 * dx + 0.5)
  
  mid20.w = mid20.x2 - mid20.x
  mid20.h = mid20.y2 - mid20.y
  mid40.w = mid40.x2 - mid40.x
  mid40.h = mid40.y2 - mid40.y
  
  return True

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  
def getGuideRects():
  global midLeft,mid20,mid40,midRight
  global topLeft,topRight,botLeft,botRight
  global studentFrame,teacherFrame
  
  #TBA .. possible need for multiple calls to get guide rect methods
  # with multiple testBinInv from different threshold offesets ...

  valid = True
  try:
    valid = getFourGuideRectsTopBottom(frame,testBin,testBinInv) and \
            getFourGuideRectsMiddle(frame,testBin,testBinInv)
  except:
    return False  

  if not valid:
    return False
 
  if not allGuideRectsValid():
    return False
  
  #draw guide rect positions to studentFrame
  cv2.rectangle(studentFrame,(botLeft.x+testOutline.x,botLeft.y+testOutline.y),(botLeft.x2+testOutline.x,botLeft.y2+testOutline.y),cyan,2)
  cv2.rectangle(studentFrame,(botRight.x+testOutline.x,botRight.y+testOutline.y),(botRight.x2+testOutline.x,botRight.y2+testOutline.y),cyan,2)
  cv2.rectangle(studentFrame,(topLeft.x+testOutline.x,topLeft.y+testOutline.y),(topLeft.x2+testOutline.x,topLeft.y2+testOutline.y),cyan,2)
  cv2.rectangle(studentFrame,(topRight.x+testOutline.x,topRight.y+testOutline.y),(topRight.x2+testOutline.x,topRight.y2+testOutline.y),cyan,2)
  
  cv2.rectangle(studentFrame,(midLeft.x+testOutline.x,midLeft.y+testOutline.y),(midLeft.x2+testOutline.x,midLeft.y2+testOutline.y),cyan,2)
  cv2.rectangle(studentFrame,(midRight.x+testOutline.x,midRight.y+testOutline.y),(midRight.x2+testOutline.x,midRight.y2+testOutline.y),cyan,2)
  cv2.rectangle(studentFrame,(mid20.x+testOutline.x,mid20.y+testOutline.y),(mid20.x2+testOutline.x,mid20.y2+testOutline.y),cyan,2)
  cv2.rectangle(studentFrame,(mid40.x+testOutline.x,mid40.y+testOutline.y),(mid40.x2+testOutline.x,mid40.y2+testOutline.y),cyan,2)
  
  teacherFrame = np.copy(studentFrame)
  
  return True

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  
def allGuideRectsValid():
  global midLeft,mid20,mid40,midRight
  global topLeft,topRight,botLeft,botRight
  global studentFrame,teacherFrame
  widthMin = 8
  widthMax = 12
  heightMin = 7
  heightMax = 12
  arrayMid = [midLeft,mid20,mid40,midRight]
  arrayEdges = [topLeft,topRight,botLeft,botRight]
  for sqr in arrayMid:
    if sqr.w >= widthMin and sqr.w <= widthMax:
        if sqr.h >= heightMin and sqr.h <= heightMax:
            continue
    return False
  for sqr in arrayEdges:
    if sqr.w >= widthMin and sqr.w <= widthMax:
        continue
    #print("false")
    return False
  #print("true")
  return True

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def writeItemAnal():
  global answerFreq
  
  #TODO .. write method to create a file for the Item Analysis
  
  pass

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def gradeAllGrids(frame,testGray):
  global totalScore,numUnanswered,answerStr, validScan
  global studentFrame,teacherFrame
  global testBin,testBinInv
  ret,testBin = cv2.threshold(testGray, threshold+threshOffset, 255, cv2.THRESH_BINARY)
  ret,testBinInv = cv2.threshold(testGray, threshold+threshOffset, 255, cv2.THRESH_BINARY_INV)
  
  answerStr = str(imageNum) + "\t~\t"
  
  grid1_10 = Rect(midLeft.x2,midLeft.y2,botLeft.x-midLeft.x2,botLeft.y-midLeft.y2)
  gradeGrid(frame,grid1_10,1)
  if numQuestions > 10:
    grid11_20 = Rect(topLeft.x2,topLeft.y2,mid40.x-topLeft.x2,mid40.y-topLeft.y2)
    gradeGrid(frame,grid11_20,11)
  if numQuestions > 20:
    grid21_30 = Rect(mid20.x2,mid20.y2,botRight.x-mid20.x2,botRight.y-mid20.y2)
    gradeGrid(frame,grid21_30,21)
  if numQuestions > 30:
    grid31_40 = Rect(topRight.x2,topRight.y2,midRight.x-topRight.x2,midRight.y-topRight.y2)
    gradeGrid(frame,grid31_40,31)
  if numQuestions > 40:
    grid41_50 = Rect(mid40.x2,mid40.y2,midRight.x-mid40.x2,botRight.y-mid40.y2)
    gradeGrid(frame,grid41_50,41)
    
  if numUnanswered > 0:
    validScan = False
    return
    
  answerList.append(answerStr)
  
  #print(answerList)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

def gradeGrid(frame,grid,startQuestion):
  global totalScore, numUnanswered, answerFreq, answerStr
  global studentFrame,teacherFrame
  global testBin,testBinInv
    
  bubbleW = (grid.x2 - grid.x) / 5.0
  bubbleH = (grid.y2 - grid.y) / 10.0
  
  #loop thru 50 bubbles .. 10x5
  for r in range(10):
    if r + startQuestion > numQuestions:
      break
    bubbleCnt = 0
    currentAns = ''
    for c in range(5):
      topX = int(c * bubbleW + 0.5) + grid.x
      topY = int(r * bubbleH + 0.5) + grid.y
      botX = int((c+1) * bubbleW + 0.5) + grid.x
      botY = int((r+1) * bubbleH + 0.5) + grid.y
        
      blackPixelCnt = len(np.flatnonzero(testBinInv[topY:botY, topX:botX]))
      #number of darkened pixels within a given bubble 
      
      if blackPixelCnt > (0.10 * bubbleW * bubbleH):
        cv2.rectangle(studentFrame, (topX+testOutline.x, topY+testOutline.y), \
        (botX+testOutline.x, botY+testOutline.y), cyan, 1)
        cv2.rectangle(teacherFrame, (topX+testOutline.x, topY+testOutline.y), \
        (botX+testOutline.x, botY+testOutline.y), cyan, 1)
        
        bubbleCnt += 1
        answerFreq[r+startQuestion][c] += 1
        currentAns += chr( ord('A') + c )
      
      #red rect mark on teacherFrame
      if answerKey[r+startQuestion].find( chr(ord('A')+c) ) > -1:
        cv2.rectangle(teacherFrame, (topX+testOutline.x+3, botY+testOutline.y-3), \
        (topX+testOutline.x+8, botY+testOutline.y-1), red, 1)
      
    #red circle around unAnswered question
    if bubbleCnt <= 0:
      ctrx = (topX + testOutline.x - int(5*bubbleW) + botX + testOutline.x - int(5*bubbleW)) // 2
      ctry = (topY + testOutline.y + botY + testOutline.y) // 2
      rad = int(bubbleW) // 2
      cv2.ellipse(studentFrame, (ctrx,ctry), (rad-1,rad-1), 0, 0, 360, red, 1)
      cv2.ellipse(teacherFrame, (ctrx,ctry), (rad-1,rad-1), 0, 0, 360, red, 1)
      
    
    if currentAns == answerKey[r+startQuestion]:
      totalScore += 1
    elif currentAns == '':
      numUnanswered += 1
    answerStr += currentAns + '\t'

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def showScoreWindow(windowName):
  global studentFrame, validScan
  global totalScore, numUnanswered, numQuestions, showScoreCnt
  
  thick = 2
  initx,inity = 50,70
  if validScan:
    initx = 50
    cv2.putText(studentFrame, "Score:",(initx+2,inity+2) , 0, 1, black, thick, cv2.LINE_AA)
    cv2.putText(studentFrame, "Score:",(initx,inity) , 0, 1, white, thick, cv2.LINE_AA)
    cv2.putText(studentFrame, "unAnswered:",(430+2,inity+2) , 0, 1, black, thick, cv2.LINE_AA)
    cv2.putText(studentFrame, "unAnswered:",(430,inity) , 0, 1, white, thick, cv2.LINE_AA)
    cv2.putText(studentFrame, str(numUnanswered),(430+4,inity+50+4) , 0, 1.5, black, thick, cv2.LINE_AA)
    cv2.putText(studentFrame, str(numUnanswered),(430+2,inity+50+2) , 0, 1.5, white, thick, cv2.LINE_AA)
    cv2.putText(studentFrame, str(numUnanswered),(430,inity+50) , 0, 1.5, red, thick+1, cv2.LINE_AA)
    
    if showScoreCnt == 180:
      thick = 6
      size = 6
      cv2.putText(teacherFrame, str(totalScore),(initx+8,inity+80+thick*2) , 0, size, black, thick, cv2.LINE_AA)
      cv2.putText(teacherFrame, str(totalScore),(initx+4,inity+80+thick) , 0, size, red, thick, cv2.LINE_AA)
      cv2.putText(teacherFrame, str(totalScore),(initx, inity+80) , 0, size, white, thick, cv2.LINE_AA)   
      
    if showScoreCnt >= 120 and showScoreCnt < 200:
      fraction = ((200 - showScoreCnt)/80)
      deg = int( fraction * 360.0 + 0.5)
      cv2.ellipse(studentFrame, (initx+50,inity+60),(50,50),0,   0,   360, red, -1)
      cv2.ellipse(studentFrame, (initx+50,inity+60),(50,50),0,   deg,  360, white, -1)
    initx = 20 
    if showScoreCnt >= 0 and showScoreCnt <= 120:
      thick = 3
      size = 2
      cv2.putText(studentFrame, str(totalScore) + "/" + str(numQuestions),(initx+2,inity+70+3) , 0, size, black, thick, cv2.LINE_AA)
      cv2.putText(studentFrame, str(totalScore) + "/" + str(numQuestions),(initx,inity+70) , 0, size, white, thick, cv2.LINE_AA)
      
  else:
    initx,inity = 30,40
    txt = "PLEASE SCAN AGAIN"
    cv2.putText(studentFrame, txt,(initx+2,inity+2) , 0, 1.4, black, thick, cv2.LINE_AA)
    cv2.putText(studentFrame, txt,(initx,inity) , 0, 1.4, white, thick, cv2.LINE_AA)
    
    if numUnanswered > 0:
      initx,inity = 50,70
      cv2.putText(studentFrame, "unAnswered:",(430+2,inity+2) , 0, 1, black, thick, cv2.LINE_AA)
      cv2.putText(studentFrame, "unAnswered:",(430,inity) , 0, 1, white, thick, cv2.LINE_AA)
      cv2.putText(studentFrame, str(numUnanswered),(430+4,inity+50+4) , 0, 1.4, black, thick, cv2.LINE_AA)
      cv2.putText(studentFrame, str(numUnanswered),(430+2,inity+50+2) , 0, 1.4, white, thick, cv2.LINE_AA)
      cv2.putText(studentFrame, str(numUnanswered),(430,inity+50) , 0, 1.4, red, thick+1, cv2.LINE_AA)
   
  cv2.imshow(windowName, studentFrame)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def showThreshWindow():
  global showThreshCnt
  global testBin,testBinInv
  showThreshCnt -= 1
  #threshold offset
  percent = 50 + threshOffset
  cv2.putText(testBin, str(percent)+'%',(50+3,50-3) , 0, 1.5, white, 3, cv2.LINE_AA)
  cv2.putText(testBin, str(percent)+'%',(50,50) , 0, 1.5, black, 3, cv2.LINE_AA)

  if showThreshCnt > 0:
    cv2.imshow('Brightness', testBin)
  if showThreshCnt == 0:
    cv2.destroyWindow("Brightness")

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

def animateSquares():
  global frame,inRangeCnt,helpAnimation,showScoreCnt
  
  if not helpAnimation and inRangeCnt < 9:
    frame[0:75,640-75:640,0:3] = logoPic75x75
  
  if not helpAnimation or showScoreCnt >= -1 or inRangeCnt >= 2:
    return
    
  c = (0,0,0)
  #c = (0,255,255) #.. yellow

  frames = 40
  numPeriods = 7
  numDelays = 2
  scl = 0.0
  ymove = 0
  txt = ""
  sclStart,sclEnd = 0.85,1.03
  sclRange = sclEnd - sclStart
  yStart,yEnd = 0,24
  yRange = yEnd - yStart
  ypos = 0

  wfwdStart,wfwdEnd = 11,17
  wfwdRange = wfwdEnd - wfwdStart
  botxfwdStart,botxfwdEnd = testOutline.x+60, testOutline.x+32
  botyfwdStart,botyfwdEnd = testOutline.y2-60, testOutline.y2-20
  botxfwdRange,botyfwdRange = abs(botxfwdEnd-botxfwdStart),botyfwdEnd-botyfwdStart
  
  botyupStart,botyupEnd = botyfwdEnd, testOutline.y2-48
  botyupRange = abs(botyupEnd-botyupStart)
  
  #wfwdStart,wfwdEnd = 11,17
  #wfwdRange = wfwdEnd - wfwdStart
  topxfwdStart,topxfwdEnd = testOutline.x2-60-wfwdStart, testOutline.x2-32-wfwdEnd
  topyfwdStart,topyfwdEnd = testOutline.y+60, testOutline.y+60
  topxfwdRange,topyfwdRange = topxfwdEnd-topxfwdStart,topyfwdEnd-topyfwdStart
  
  topyupStart,topyupEnd = topyfwdEnd, testOutline.y+32
  topyupRange = abs(botyupEnd-botyupStart)
   
  #  0     1     2     3      4      5    6   7
  #delay,delay,delay,pause,forward,pause,up,pause
  period = -showScoreCnt % (numPeriods*frames)
  
  if period // frames >= 0 and period // frames <= 1:
    return
  
  initypos = 20
  #pause
  if period // frames == numDelays + 0:
    scl = sclStart
    ypos = testOutline.y + initypos
    txt = ""
    botxfwdScl = botxfwdStart
    bot = Rect (botxfwdStart, botyfwdStart, wfwdStart,wfwdStart)
    cv2.rectangle(frame, (bot.x,bot.y), (bot.x2,bot.y2), c, -1)
    top = Rect (topxfwdStart, topyfwdStart, wfwdStart,wfwdStart)
    cv2.rectangle(frame, (top.x,top.y), (top.x2,top.y2), c, -1)  

  #forward
  if period // frames == numDelays + 1:
    scl = sclStart + sclRange * (period % frames)/frames
    ypos = testOutline.y + initypos
    txt = "FORWARD"
    bot = Rect (botxfwdStart-int(botxfwdRange * (period % frames)/frames+0.5), \
                botyfwdStart+int(botyfwdRange * (period % frames)/frames+0.5), \
                wfwdStart+int(wfwdRange * (period % frames)/frames+0.5), \
                wfwdStart+int(wfwdRange * (period % frames)/frames+0.5) )
    top = Rect (topxfwdStart+int(topxfwdRange * (period % frames)/frames+0.5), \
                topyfwdStart, \
                wfwdStart+int(wfwdRange * (period % frames)/frames+0.5), \
                wfwdStart+int(wfwdRange * (period % frames)/frames+0.5) )
    cv2.rectangle(frame, (bot.x,bot.y), (bot.x2,bot.y2), c, -1)
    cv2.rectangle(frame, (top.x,top.y), (top.x2,top.y2), c, -1)

  #pause  
  if period // frames == numDelays + 2:
    scl = sclEnd
    ypos = testOutline.y + initypos
    txt = ""
    bot = Rect (botxfwdEnd, botyupStart, wfwdEnd,wfwdEnd)
    cv2.rectangle(frame, (bot.x,bot.y), (bot.x2,bot.y2), c, 2)
    top = Rect (topxfwdEnd, topyupStart, wfwdEnd,wfwdEnd)
    cv2.rectangle(frame, (top.x,top.y), (top.x2,top.y2), c, 2)  

  #up  
  if period // frames == numDelays + 3:
    scl = sclEnd
    ymove = yRange * (period % frames)/frames
    ypos = testOutline.y + initypos - int(ymove + 0.5)
    txt = "   UP"
    bot = Rect (botxfwdEnd, botyupStart-int(botyupRange * (period % frames)/frames+0.5), \
                wfwdEnd,wfwdEnd)
    top = Rect (topxfwdEnd, topyupStart-int(topyupRange * (period % frames)/frames+0.5), \
                wfwdEnd,wfwdEnd)
    cv2.rectangle(frame, (bot.x,bot.y), (bot.x2,bot.y2), c, 2)
    cv2.rectangle(frame, (top.x,top.y), (top.x2,top.y2), c, 2)  

  #pause  
  if period // frames == numDelays + 4:
    scl = sclEnd
    ypos = testOutline.y + initypos  - yEnd
    txt = ""
    bot = Rect (botxfwdEnd, botyupEnd, wfwdEnd,wfwdEnd)
    cv2.rectangle(frame, (bot.x,bot.y), (bot.x2,bot.y2), c, 2)
    top = Rect (topxfwdEnd, topyupEnd, wfwdEnd,wfwdEnd)
    cv2.rectangle(frame, (top.x,top.y), (top.x2,top.y2), c, 2)  
  
  outer = Rect( testOutline.x + int(testOutline.w * (1.0-scl) / 2.0 + 0.5), ypos, \
                int(testOutline.w * scl + 0.5), \
                int(testOutline.h * scl + 0.5) )
  cv2.rectangle(frame, (outer.x,outer.y), (outer.x2,outer.y2), c, 2)  
  
  initx,inity = 20,100
  thick = 2
  cv2.putText(frame, txt,(initx+2,inity+2) , 0, 1.4, black, thick, cv2.LINE_AA)
  cv2.putText(frame, txt,(initx,inity) , 0, 1.4, white, thick, cv2.LINE_AA)
  cv2.putText(frame, txt,(initx+2+400,inity+2) , 0, 1.4, black, thick, cv2.LINE_AA)
  cv2.putText(frame, txt,(initx+400,inity) , 0, 1.4, white, thick, cv2.LINE_AA)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN program ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
  
clf = cv2.CascadeClassifier('./haarcascade_frontalface_default.xml')

runProgram = True
try:
  camera = cv2.VideoCapture(0)
  camera.set(3,640);
  camera.set(4,480);
  readAnswerKey()
except:
  runProgram = False

try:
  logoPic150x150 = cv2.imread("logo150x150.png",cv2.IMREAD_COLOR)
  logoPic75x75 = cv2.resize(logoPic150x150,(75,75))
except:
  pass

if runProgram:
  initSaveDirectory()
  cv2.namedWindow(windowTitle, cv2.WINDOW_NORMAL)
  cv2.resizeWindow(windowTitle, int(640*1.25),int(480*1.25))
  cv2.moveWindow(windowTitle, 240,0 )

while runProgram: #main program loop
  ret, frame = camera.read() #frame capture is 640x480
  
  testGray = cv2.cvtColor(frame[testOutline.y:testOutline.y2,testOutline.x:testOutline.x2, :3], cv2.COLOR_BGR2GRAY)
  ret,testBin = cv2.threshold(testGray, threshold+threshOffset, 255, cv2.THRESH_BINARY)
  ret,testBinInv = cv2.threshold(testGray, threshold+threshOffset, 255, cv2.THRESH_BINARY_INV)
  
  frame = cv2.flip(frame,1) #reflect over vertical center line
  animateSquares()
  
  cv2.ellipse(frame, (320,100), (70,90), 0, 0, 360, red, 2)
  #test rect 350x270 (approx 8.5x11 paper)
  cv2.rectangle(frame, (testOutline.x,testOutline.y), (testOutline.x2,testOutline.y2), red, 2)
  
  #guide squares 20x20
  cv2.rectangle(frame, (topGuideSqr.x,topGuideSqr.y), (topGuideSqr.x2,topGuideSqr.y2), red, 2)
  cv2.rectangle(frame, (botGuideSqr.x,botGuideSqr.y), (botGuideSqr.x2,botGuideSqr.y2), red, 2)
  
  #guide squares guide rails
  cv2.line(frame, (topGuideSqr.x,topGuideSqr.y2), (topGuideSqr.x,topGuideSqr.y2 + 30), red, 1)
  cv2.line(frame, (topGuideSqr.x-1,topGuideSqr.y2), (topGuideSqr.x-1,topGuideSqr.y2 + 30), cyan, 1)
  
  cv2.line(frame, (topGuideSqr.x2,topGuideSqr.y2), (topGuideSqr.x2,topGuideSqr.y2 + 30), red, 1)
  cv2.line(frame, (topGuideSqr.x2+1,topGuideSqr.y2), (topGuideSqr.x2+1,topGuideSqr.y2 + 30), cyan, 1)

  cv2.line(frame, (botGuideSqr.x,botGuideSqr.y2), (botGuideSqr.x,botGuideSqr.y2 + 30), red, 1)
  cv2.line(frame, (botGuideSqr.x-1,botGuideSqr.y2), (botGuideSqr.x-1,botGuideSqr.y2 + 30), cyan, 1)
  
  cv2.line(frame, (botGuideSqr.x2,botGuideSqr.y2), (botGuideSqr.x2,botGuideSqr.y2 + 30), red, 1)
  cv2.line(frame, (botGuideSqr.x2+1,botGuideSqr.y2), (botGuideSqr.x2+1,botGuideSqr.y2 + 30), cyan, 1)

  
  if faceInRangeOn:
    faceInRange = isFaceInRange(frame)
  else:
    faceInRange = True
    cv2.ellipse(frame, (320,100), (70,90), 0, 0, 360, cyan, 3) #face oval

  testInRange = isTestInRange(frame,testBin,testBinInv)
  if faceInRange and testInRange and showScoreCnt < 0:
    inRangeCnt += 1
    if inRangeCnt == 10:
      totalScore,numUnanswered = 0,0
      validScan = False
      studentFrame = np.copy(frame)
      studentFrame = cv2.flip(studentFrame,1)
      validScan = getGuideRects()
      if validScan:
        gradeAllGrids(frame,testGray)
        showScoreCnt = 200 #show graded test window
      else:
        showScoreCnt = 100 #show 'PLEASE SCAN AGAIN'      
  else:
    inRangeCnt = 0
    
  frameCnt += 1   
  showScoreCnt -= 1
  
  cv2.imshow(windowTitle, frame)
 
  if showScoreCnt > 0:
    windowName = 'Score Frame'
    showScoreWindow(windowName)
  if showScoreCnt == 160 and validScan:
    cv2.imwrite(directory+'\\student'+str(imageNum)+'.jpg',teacherFrame)
    imageNum += 1
  if showScoreCnt == 0:
    showScoreCnt -= 1
    try:
      cv2.destroyWindow(windowName)
    except:
      pass

  showThreshWindow()
    
  keyCode = cv2.waitKey(1) #1 millisecond 
  if keyCode == ord('+') or keyCode == ord('='): 
    threshOffset += 1
    showThreshCnt = 120
  if keyCode == ord('-'): 
    threshOffset -= 1
    showThreshCnt = 120
  if keyCode == ord('F') or keyCode == ord('f'):
    faceInRangeOn = not faceInRangeOn
  if keyCode == ord('A') or keyCode == ord('a'):
    helpAnimation = not helpAnimation
  if keyCode == ord(' ') and showScoreCnt < 0:
    showScoreCnt = 150
    #set showScoreCnt to display the previous studentFrame for 150 ticks
    
  if keyCode == 27 or keyCode == ord('q'): #escape key or 'q'
      break
  
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~ END program ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
if runProgram:
  ff = open(directory + '\\answerList.txt','w')
  for line in answerList:
    temp = line[0:-1]
    #print(temp)
    ff.write("%s\n" % temp)
  ff.close()  

  camera.release()
  cv2.destroyAllWindows()
