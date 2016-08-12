#!/usr/bin/env python2
import json
import math
import os
import logging
import time
import geojson

import threading
import utils

from pgoapi import pgoapi
from pgoapi import utilities as util
from pgoapi.exceptions import NotLoggedInException, ServerSideRequestThrottlingException, ServerBusyOrOfflineException, AuthException

from s2sphere import CellId, LatLng

pokes = {}
spawns = {}
stops = {}
gyms = {}

scans = []
num2words = ['first','second','third','fourth','fifth','sixth']

#config file
with open('config.json') as file:
    config = json.load(file)

def doScanp(wid, sLat, sLng, api):
    for i in range(0,10):
        try:
            doScan(wid, sLat, sLng, api)
        except (KeyError,TypeError):
            print('thread {} error scan returned error, retry {}/10').format(wid,i)
            time.sleep(config['scanDelay'])
            continue
        else:
            print("")

def doScan(wid, sLat, sLng, api):
    #print ('scanning ({}, {})'.format(sLat, sLng))
    api.set_position(sLat,sLng,0)
    cell_ids = util.get_cell_ids(lat=sLat, long=sLng, radius=80)
    timestamps = [0,] * len(cell_ids)
    while True:
        try:
            response_dict = api.get_map_objects(latitude = sLat, longitude = sLng, since_timestamp_ms = timestamps, cell_id = cell_ids)
        except  ServerSideRequestThrottlingException:
            config['scanDelay'] += 0.5
            print ('Request throttled, increasing sleep by 0.5 to {}').format(config['scanDelay'])
            time.sleep(config['scanDelay'])
            continue
        except:
            time.sleep(config['scanDelay'])
            api.set_position(sLat,sLng,0)
            time.sleep(config['scanDelay'])
            continue
        break
        
    try:
        cells = response_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    except TypeError:
        print ('thread {} error getting map data for {}, {}'.format(wid,sLat, sLng))
        raise
    except KeyError:
        print ('thread {} error getting map data for {}, {}'.format(wid,sLat, sLng))
        raise
        return
    for cell in cells:
        curTime = cell['current_timestamp_ms']
        if 'wild_pokemons' in cell:
            for wild in cell['wild_pokemons']:
                if wild['time_till_hidden_ms']>0:
                    timeSpawn = (curTime+(wild['time_till_hidden_ms']))-900000
                    gmSpawn = time.gmtime(int(timeSpawn/1000))
                    secSpawn = (gmSpawn.tm_min*60)+(gmSpawn.tm_sec)
                    phash = '{},{}'.format(timeSpawn,wild['spawn_point_id'])
                    shash = '{},{}'.format(secSpawn,wild['spawn_point_id'])
                    pokeLog = {'time':timeSpawn, 'sid':wild['spawn_point_id'], 'lat':wild['latitude'], 'lng':wild['longitude'], 'pid':wild['pokemon_data']['pokemon_id'], 'cell':CellId.from_lat_lng(LatLng.from_degrees(wild['latitude'], wild['longitude'])).to_token()}
                    spawnLog = {'time':secSpawn, 'sid':wild['spawn_point_id'], 'lat':wild['latitude'], 'lng':wild['longitude'], 'cell':CellId.from_lat_lng(LatLng.from_degrees(wild['latitude'], wild['longitude'])).to_token()}
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
    time.sleep(config['scanDelay'])

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

def login(auth, username, password):
        while True:
            try:
                time.sleep(1)
                global LoginApi
                LoginApi = pgoapi.PGoApi(provider=auth, username=username, password=password, position_lat=0, position_lng=0, position_alt=0)
                time.sleep(10)
                break;
            except  AuthException:
                print("Could not retrieve a PTC Access Token, Waiting 10 seconds and trying again.")
                time.sleep(10)
                pass

def worker(wid,Wstart):
    workStart = min(Wstart,len(scans)-1)
    workStop = min(Wstart+config['stepsPerPassPerWorker'],len(scans)-1)
    if workStart == workStop:
        return
    print 'worker {} is doing steps {} to {}'.format(wid,workStart,workStop)
    #login
    login(config['auth_service'], config['users'][wid]['username'], config['users'][wid]['password'])
    LoginApi.get_player()
    #iterate
    for j in range(5):
        startTime = time.time()
        print 'worker {} is doing {} pass'.format(wid,num2words[j])
        for i in xrange(workStart,workStop):
            doScanp(wid,scans[i][0], scans[i][1], LoginApi)
        curTime=time.time()
        if 600-(curTime-startTime) > 0:
            print 'worker {} took {} seconds to do {} pass, now sleeping for {}'.format(wid,curTime-startTime,num2words[j],600-(curTime-startTime))
            time.sleep(600-(curTime-startTime))
        else:
            print 'worker {} took {} seconds to do {} pass so not sleeping'.format(wid,curTime-startTime,num2words[j])
    startTime = time.time()
    print 'worker {} is doing {} pass'.format(wid,num2words[5])
    for i in xrange(workStart,workStop):
        doScanp(wid,scans[i][0], scans[i][1], LoginApi)
    curTime=time.time()
    print 'worker {} took {} seconds to do {} pass ending thread'.format(wid,curTime-startTime,num2words[5])

def main():
    tscans = genwork()
    print 'total of {} steps'.format(tscans)
    numWorkers = ((tscans-1)//config['stepsPerPassPerWorker'])+1
    if numWorkers > len(config['users']):
        numWorkers = len(config['users'])
    if config['scanDelay'] < 10:
        config['scanDelay'] = 10
    print 'with {} worker(s), doing {} scans each, would take {} hour(s)'.format(numWorkers,config['stepsPerPassPerWorker'],int(math.ceil(float(tscans)/(numWorkers*config['stepsPerPassPerWorker']))))
    if (config['stepsPerPassPerWorker']*config['scanDelay']) > 600:
        print 'error. scan will take more than 10mins so all 6 scans will take more than 1 hour'
        print 'please try using less scans per worker'
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

    threads = []
    scansStarted = 0
    for i in xrange(len(config['users'])):
        if scansStarted >= len(scans):
            break;
        t = threading.Thread(target=worker, args = (i,scansStarted))
        t.start()
        threads.append(t)
        scansStarted += config['stepsPerPassPerWorker']
    while scansStarted < len(scans):
        time.sleep(15)
        for i in xrange(len(threads)):
            if not threads[i].isAlive():
                threads[i] = threading.Thread(target=worker, args = (i,scansStarted))
                threads[i].start()
                scansStarted += config['stepsPerPassPerWorker']
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
