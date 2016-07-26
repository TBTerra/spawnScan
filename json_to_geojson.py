import json
import geojson
import pprint

with open('gyms.json') as file:
	gyms = json.load(file)

geostops = []
for location in gyms:
	point = geojson.Point((location['lng'], location['lat']))
	feature = geojson.Feature(geometry=point, id=location['id'],properties={"name":location['id']})
	geostops.append(feature)
features = geojson.FeatureCollection(geostops)
f = open('geo_gyms.json', 'w')
json.dump(features,f)
f.close()


with open('stops.json') as file:
	stops = json.load(file)

geostops = []
for location in stops:
	point = geojson.Point((location['lng'], location['lat']))
	feature = geojson.Feature(geometry=point, id=location['id'],properties={"name":location['id']})
	geostops.append(feature)
features = geojson.FeatureCollection(geostops)
f = open('geo_stops.json', 'w')
json.dump(features,f)
f.close()
