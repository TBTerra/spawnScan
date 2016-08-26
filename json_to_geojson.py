import json
import geojson
import pprint

def convert_to_geojson(infile, outfile):
    with open(infile) as file:
        items = json.load(file)
    geoitems = []
    for location in items:
        point = geojson.Point((location['lng'], location['lat']))
        feature = geojson.Feature(geometry=point,
                    id=location['id'], properties={ "name": location['id'] })
        geoitems.append(feature)
    features = geojson.FeatureCollection(geoitems)
    f = open(outfile, 'w')
    json.dump(features, f)
    f.close()


if __name__ == "__main__":
    convert_to_geojson('gyms.json', 'geo_gyms.json')
    convert_to_geojson('stops.json', 'geo_stops.json')
