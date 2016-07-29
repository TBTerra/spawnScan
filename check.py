import json
import math

with open('config.json') as file:
	config = json.load(file)

def calcwork():
	totalwork = 0
	area = 0
	for rect in config['work']:
		distN = math.radians(max(rect[0], rect[2])-min(rect[0], rect[2]))*6371
		distE = math.radians(max(rect[3], rect[1])-min(rect[3], rect[1]))*6371*math.cos(math.radians((rect[0]+rect[2])*0.5))
		dlat = 0.00089
		dlng = dlat / math.cos(math.radians((rect[0]+rect[2])*0.5))
		latSteps = int((((max(rect[0], rect[2])-min(rect[0], rect[2])))/dlat)+0.75199999)
		if latSteps<1:
			latSteps=1
		lngSteps = int((((max(rect[1], rect[3])-min(rect[1], rect[3])))/dlng)+0.75199999)
		if lngSteps<1:
			lngSteps=1
		totalwork += latSteps * lngSteps
		area += distN * distE
	return totalwork, area

tscans,tarea = calcwork()
print 'total of {} steps covering {} km^2, approx {} seconds for scan'.format(tscans,tarea,tscans/(2.25*len(config['users'])))
