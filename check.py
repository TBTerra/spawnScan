import json
import math

with open('config.json') as file:
	config = json.load(file)

def calcwork():
	totalwork = 0
	area = 0
	for rect in config['work']:
		distN = math.radians(rect[0]-rect[2])*6371
		distE = math.radians(rect[3]-rect[1])*6371*math.cos(math.radians((rect[0]+rect[2])*0.5))
		dlat = 0.6*0.00225
		dlng = dlat / math.cos(math.radians((rect[0]+rect[2])*0.5))
		latSteps = int((((rect[0]-rect[2]))/dlat)+0.75199999)
		if latSteps<1:
			latSteps=1
		lngSteps = int((((rect[3]-rect[1]))/dlng)+0.75199999)
		if lngSteps<1:
			lngSteps=1
		totalwork += latSteps * lngSteps
		area += distN * distE
	return totalwork, area

tscans,tarea = calcwork()
print 'total of {} steps covering {} km^2, approx {} seconds for scan'.format(tscans,tarea,tscans/(2.25*len(config['users'])))