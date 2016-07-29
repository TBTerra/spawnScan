import json
import math
import os
import logging
import time
import geojson

import threading

from pgoapi import PGoApi
from pgoapi.utilities import f2i

from google.protobuf.internal import encoder
from s2sphere import CellId, LatLng

pokes = {}
spawns = {}
stops = {}
gyms = {}

scans = []

#config file
with open('config.json') as file:
	config = json.load(file)

def get_cellid(lat, long):
	origin = CellId.from_lat_lng(LatLng.from_degrees(lat, long)).parent(15)
	walk = [origin.id()]

	# 10 before and 10 after
	next = origin.next()
	prev = origin.prev()
	for i in range(10):
		walk.append(prev.id())
		walk.append(next.id())
		next = next.next()
		prev = prev.prev()
	return ''.join(map(encode, sorted(walk)))

def encode(cellid):
	output = []
	encoder._VarintEncoder()(output.append, cellid)
	return ''.join(output)

def doScan(sLat, sLng, api):
	#print ('scanning ({}, {})'.format(sLat, sLng))
	api.set_position(sLat,sLng,0)
	timestamp = "\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
	cellid = get_cellid(sLat, sLng)
	api.get_map_objects(latitude=f2i(sLat), longitude=f2i(sLng), since_timestamp_ms=timestamp, cell_id=cellid)
	response_dict = api.call()
	try:
		cells = response_dict['responses']['GET_MAP_OBJECTS']['map_cells']
	except TypeError:
		print ('error getting map data for {}, {}'.format(sLat, sLng))
		return
	except KeyError:
		print ('error getting map data for {}, {}'.format(sLat, sLng))
		return
	for cell in cells:
		curTime = cell['current_timestamp_ms']
		if 'wild_pokemons' in cell:
			for wild in cell['wild_pokemons']:
				if wild['time_till_hidden_ms']>0:
					timeSpawn = (curTime+(wild['time_till_hidden_ms']))-900000
					gmSpawn = time.gmtime(int(timeSpawn/1000))
					secSpawn = (gmSpawn.tm_min*60)+(gmSpawn.tm_sec)
					phash = '{},{}'.format(timeSpawn,wild['spawnpoint_id'])
					shash = '{},{}'.format(secSpawn,wild['spawnpoint_id'])
					pokeLog = {'time':timeSpawn, 'sid':wild['spawnpoint_id'], 'lat':wild['latitude'], 'lng':wild['longitude'], 'pid':wild['pokemon_data']['pokemon_id'], 'cell':CellId.from_lat_lng(LatLng.from_degrees(wild['latitude'], wild['longitude'])).to_token()}
					spawnLog = {'time':secSpawn, 'sid':wild['spawnpoint_id'], 'lat':wild['latitude'], 'lng':wild['longitude'], 'cell':CellId.from_lat_lng(LatLng.from_degrees(wild['latitude'], wild['longitude'])).to_token()}
					pokes[phash] = pokeLog
					spawns[shash] = spawnLog
		if 'forts' in cell:
			for fort  in cell['forts']:
				if fort['enabled'] == True:
					if 'type' in fort:
						#got a pokestop
						stopLog = {'id':fort['id'],'lat':fort['latitude'],'lng':fort['longitude'],'lure':-1}
						if 'lure_info' in fort:
							stopLog['lure'] = fort['lure_info']['lure_expires_timestamp_ms']
						stops[fort['id']] = stopLog
					if 'gym_points' in fort:
						gymLog = {'id':fort['id'],'lat':fort['latitude'],'lng':fort['longitude'],'team':0}
						if 'owned_by_team' in fort:
							gymLog['team'] = fort['owned_by_team']
						gyms[fort['id']] = gymLog

def genwork():
	totalwork = 0
	for rect in config['work']:
		dlat = 0.00089
		dlng = dlat / math.cos(math.radians((rect[0]+rect[2])*0.5))
		startLat = min(rect[0], rect[2])+(0.624*dlat)
		startLng = min(rect[1], rect[3])+(0.624*dlng)
		latSteps = int((((max(rect[0], rect[2])-min(rect[0], rect[2])))/dlat)+0.75199999)
		if latSteps<1:
			latSteps=1
		lngSteps = int((((max(rect[1], rect[3])-min(rect[1], rect[3])))/dlng)+0.75199999)
		if lngSteps<1:
			lngSteps=1
		for i in range(latSteps):
			for j in range(lngSteps):
				scans.append([startLat+(dlat*i), startLng+(dlng*j)])
		totalwork += latSteps * lngSteps
	return totalwork

def worker(wid,Tthreads):
	workStart = int((wid*len(scans))/Tthreads)
	workStop = int(((wid+1)*len(scans))/Tthreads)
	print 'worker {} is doing steps {} to {}'.format(wid,workStart,workStop)
	#login
	api = PGoApi()
	api.set_position(0,0,0)
	if not api.login(config['auth_service'], config['users'][wid]['username'], config['users'][wid]['password']):
		print 'worker {} unable to log in'.format(wid)
		return
	#iterate
	startTime = time.time()
	print 'worker {} is doing first pass'.format(wid)
	for i in xrange(workStart,workStop):
		doScan(scans[i][0], scans[i][1], api)
		time.sleep(0.2)
	curTime=time.time()
	print 'worker {} took {} seconds to do first pass now sleeping for {}'.format(wid,curTime-startTime,600-(curTime-startTime))
	time.sleep(600-(curTime-startTime))
	print 'worker {} is doing second pass'.format(wid)
	for i in xrange(workStart,workStop):
		doScan(scans[i][0], scans[i][1], api)
		time.sleep(0.2)
	curTime=time.time()
	print 'worker {} took {} seconds to do second pass now sleeping for {}'.format(wid,curTime-startTime,1200-(curTime-startTime))
	time.sleep(1200-(curTime-startTime))
	print 'worker {} is doing third pass'.format(wid)
	for i in xrange(workStart,workStop):
		doScan(scans[i][0], scans[i][1], api)
		time.sleep(0.2)
	curTime=time.time()
	print 'worker {} took {} seconds to do third pass now sleeping for {}'.format(wid,curTime-startTime,1800-(curTime-startTime))
	time.sleep(1800-(curTime-startTime))
	print 'worker {} is doing fourth pass'.format(wid)
	for i in xrange(workStart,workStop):
		doScan(scans[i][0], scans[i][1], api)
		time.sleep(0.2)
	curTime=time.time()
	print 'worker {} took {} seconds to do fourth pass now sleeping for {}'.format(wid,curTime-startTime,2400-(curTime-startTime))
	time.sleep(2400-(curTime-startTime))
	print 'worker {} is doing fifth pass'.format(wid)
	for i in xrange(workStart,workStop):
		doScan(scans[i][0], scans[i][1], api)
		time.sleep(0.2)
	curTime=time.time()
	print 'worker {} took {} seconds to do fifth pass now sleeping for {}'.format(wid,curTime-startTime,3000-(curTime-startTime))
	time.sleep(3000-(curTime-startTime))
	print 'worker {} is doing sixth pass'.format(wid)
	for i in xrange(workStart,workStop):
		doScan(scans[i][0], scans[i][1], api)
		time.sleep(0.2)
	curTime=time.time()
	print 'worker {} took {} seconds to do sixth pass'.format(wid,curTime-startTime)

def main():
	tscans = genwork()
	print 'total of {} steps, approx {} seconds for scan'.format(tscans,tscans/(2.25*len(config['users'])))
	if (tscans/(2.25*len(config['users']))) > 600:
		print 'error. scan will take more than 10mins so all 6 scans will take more than 1 hour'
		print 'please try scanning a smaller area'
		return
#heres the logging setup
	# log settings
	# log format
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
	# log level for http request class
	logging.getLogger("requests").setLevel(logging.WARNING)
	# log level for main pgoapi class
	logging.getLogger("pgoapi").setLevel(logging.WARNING)
	# log level for internal pgoapi class
	logging.getLogger("rpc_api").setLevel(logging.WARNING)
	
	if config['auth_service'] not in ['ptc', 'google']:
		log.error("Invalid Auth service specified! ('ptc' or 'google')")
		return None
#setup done

#output
	threads = []
	for user in config['users']:
		t = threading.Thread(target=worker, args = (len(threads),len(config['users'])))
		t.start()
		threads.append(t)
	for t in threads:
		t.join()
	print 'all done. saving data'

	out = []
	for poke in pokes.values():
		out.append(poke)
	f = open('pokes.json','w')
	json.dump(out,f)
	f.close()

	out = []
	for poke in spawns.values():
		out.append(poke)
	f = open('spawns.json','w')
	json.dump(out,f)
	f.close()

	out = []
	for poke in stops.values():
		out.append(poke)
	f = open('stops.json','w')
	json.dump(out,f)
	f.close()

	out = []
	for poke in gyms.values():
		out.append(poke)
	f = open('gyms.json','w')
	json.dump(out,f)
	f.close()

#output GeoJSON data
	with open('gyms.json') as file:
		items = json.load(file)
	geopoints = []
	for location in items:
		point = geojson.Point((location['lng'], location['lat']))
		feature = geojson.Feature(geometry=point, id=location['id'],properties={"name":location['id']})
		geopoints.append(feature)
	features = geojson.FeatureCollection(geopoints)
	f = open('geo_gyms.json','w')
	json.dump(features,f)
	f.close()

	with open('stops.json') as file:
		items = json.load(file)
	geopoints = []
	for location in items:
		point = geojson.Point((location['lng'], location['lat']))
		feature = geojson.Feature(geometry=point, id=location['id'],properties={"name":location['id']})
		geopoints.append(feature)
	features = geojson.FeatureCollection(geopoints)
	f = open('geo_stops.json','w')
	json.dump(features,f)
	f.close()

if __name__ == '__main__':
	main()
