# spawnScan 0.2.5(mostly stable)(updated for 6st aug patch[unknown 6])
Now has customisable rate-limiting, a handler for oversized scans, and takes account of the 70m search radius

## A simple and fast spawnPoint finder for pokemon go
### Features
- By performing 6 scans over the course of 1 hour, the spawn locations for a given area can be determined and a live map of active spawns can be made without having to further query the api, lowering server load
- Rectangle search areas, and multiple of them
- The scans take account of longitude distortion, so requests are equally spaced (was not the case in early mapping tools causing them to perform badly near the equator because their requests where too spread out)
- High speed scans while still maintaining maximum accuracy (many scan patterns where tested and this is using the fastest of the ones with over 98% accuracy)
- Multi thread support, allowing for faster, and thus forth bigger scans (up to at least 24 workers)
- if a scan is too large to complete in 1 go, it will be divided up and processed over multiple hours if needed

### Usage
Everything is set using the config.json file, in this you put account details, and rectangular regions to scan
There are three runnable scripts, tos.py, check.py, and spawn.py
- tos.py accepts the tos on all accounts listed in config.json
- check.py checks the config file is valid json, and estimates how long the scan will take to finish
- spawn.py is the main script that does all the heavy work, finding the spawns

Also note that spawn.py overwrites its output files each run, so do back them up

If you would like to help contribute data, please send a ziped copy of the output files [pokes.json,spawns.json,stops.json,gyms.json] via private message, to reddit user TBTerra

### Maps
when veiwed localy maps will only work in firefox, however they will work in any browser when on a webserver

The maps will not work by default as you will have to use your own maps API key

To get an API key visit [this page](https://developers.google.com/maps/documentation/javascript/get-api-key) and click on get key

You will then need to go into each of the html files and at the bottom find a line like
```
src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap">
```
and you will need to replace YOUR_API_KEY with your own API key

The map of the spawn points will try to update its markers once per second, while this is fine on modern PCs on maps with a few thousand points, it may become slow on less powerful systems and on maps with far more points

### Recommended method
The recommended way to use this script is first to plan out your scan area, using viewWork.html to visualise it, and check.py to make sure it wont take too long

remember to run tos.py if your scanning accounts have not yet accepted the ingame tos

After that run spawn.py and wait for it to complete

Then enjoy the map of the spawn points

If you would like to help contribute data, please send a ziped copy of the output files [pokes.json,spawns.json,stops.json,gyms.json] via private message, to reddit user TBTerra
