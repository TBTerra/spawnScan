#!/usr/bin/env python2
"""
Inspect and/or merge multiple spawns.json files comparing the files for
inconsistencies.

This might be useful when scanning the same area multiple
times and detect if something has changed or to concatenate the scanning results
from different places.
"""
import argparse
import copy
import itertools
import json
import sys

from json_to_geojson import convert_to_geojson


def add_filename(spawn_point, filename):
    spawn_point["filename"] = filename
    return spawn_point

def print_filetimes(filetimes):
    for fn, ts in filetimes.iteritems():
        print "  %s: [%s]" % (fn, ", ".join([str(x) for x in sorted(ts)]))

def merge_stops(data, files, args):
    ids = []
    merged = []
    total = 0
    total_uniq = 0
    for stop in itertools.chain(*data):
        total += 1
        lat = stop.pop("lat")
        lng = stop.pop("lng")
        lure = stop.pop("lure")
        sid = stop.pop("id")
        try:
            found = ids.index(sid)
        except ValueError, e:
            total_uniq += 1
            ids.append(sid)
            merged.append({ 'lat':lat, 'lng':lng, 'lure':lure, 'id':sid })
    print "%s pokestops read" % total
    print "%s unique pokestops" % total_uniq
    if args.merge:
        with open(args.out, "w") as out:
            json.dump(merged, out)
        print "Wrote merged pokestops to %s" % out.name
        filename = "geo_%s" % args.out
        convert_to_geojson(args.out, filename)
        print "Wrote merged geo pokestops to %s" % filename


def merge_gyms(data, files, args):
    gids = []
    merged_gyms = []
    total_nbr_gyms = 0
    total_nbr_unique_gyms = 0
    for gym in itertools.chain(*data):
        total_nbr_gyms += 1
        lat = gym.pop("lat")
        lng = gym.pop("lng")
        gid = gym.pop("id")
        team = gym.pop("team")
        try:
            found = gids.index(gid)
        except ValueError, e:
            total_nbr_unique_gyms += 1
            gids.append(gid)
            merged_gyms.append({ 'lat':lat, 'lng':lng, 'id':gid, 'team':team })
    print "%s gyms read" % total_nbr_gyms
    print "%s unique gyms" % total_nbr_unique_gyms
    if args.merge:
        with open(args.out, "w") as out:
            json.dump(merged_gyms, out)
        print "Wrote merged gyms to %s" % out.name
        filename = "geo_%s" % args.out
        convert_to_geojson(args.out, filename)
        print "Wrote merged geo gyms to %s" % filename


def merge_spawns(data, files, args):
    # This hold all recorded spawn points with extra information about all recorded
    # spawn times and which input files it existed in
    #
    # sid: {
    #  sp: {lat,lng,sid,cell},
    #  times: set(time, ...),
    #  filetimes: {filename: set(time, ...)}
    # }
    spawn_points = {}
    merged_spawns = []
    total_nbr_spawn_points = 0

    for spawn_point in itertools.chain(*data):
        total_nbr_spawn_points += 1
        time = spawn_point.pop("time")
        filename = spawn_point.pop("filename")
        sp = spawn_points.setdefault(spawn_point.get("sid"),
            dict(sp=spawn_point, times=set(), filetimes=dict()))
        sp.get("times").add(time)
        filetimes = sp.get("filetimes").setdefault(filename, set())
        filetimes.add(time)

    total_nbr_unique_spawn_points = len(spawn_points)
    count_file_occurrence_inconsistencies = 0
    count_multiple_times = 0
    count_file_times_inconsistencies = 0

    for sid, sp in spawn_points.iteritems():
        spawn_point = sp.get("sp")
        filetimes = sp.get("filetimes")
        times = sorted(sp.get("times"))

        # Check if this spawn point was not recorded in all files
        if len(filetimes) < len(files):
            count_file_occurrence_inconsistencies += 1
            if args.show_file_occurrence_inconsistencies:
                print "! %(sid)s [%(lat)s, %(lng)s] =>" % spawn_point
                print_filetimes(filetimes)

        # Check if more than one time was found for this spawn point
        if len(times) > 1:
            count_multiple_times += 1
            if args.show_multiple_times:
                print "# %(sid)s [%(lat)s, %(lng)s] =>" % spawn_point
                for idx, t in enumerate(times):
                    line = "  %s" % t
                    if idx > 0:
                        diff = t - times[idx-1]
                        line += " (diff: %s)" % diff
                    print line
                print_filetimes(filetimes)

            # Check if the times recorded in the different files differ for spawn point
            if not all(x == sp.get("times") for x in filetimes.values()):
                count_file_times_inconsistencies += 1
                if args.show_file_times_inconsistencies:
                    print "%% %(sid)s [%(lat)s, %(lng)s] =>" % spawn_point
                    print_filetimes(filetimes)

        if args.merge:
            for t in times:
                new_spawn_point = copy.copy(spawn_point)
                new_spawn_point["time"] = t
                merged_spawns.append(new_spawn_point)

    print "%s spawn points read" % total_nbr_spawn_points
    print "%s unique spawn points" % total_nbr_unique_spawn_points
    print "%s (%.2f%%) spawn points had multiple spawn times (show with --mt, # prefix)" % (
        count_multiple_times, float(count_multiple_times)/total_nbr_unique_spawn_points*100)
    print "%s (%.2f%%) spawn points didn't occur in all files (show with --fi, ! prefix)" % (
        count_file_occurrence_inconsistencies,
        float(count_file_occurrence_inconsistencies)/total_nbr_unique_spawn_points*100)
    print "%s (%.2f%%) spawn points didn't have the same time(s) for each spawn point in all files (show with --fti, %% prefix)" % (
        count_file_times_inconsistencies,
        float(count_file_times_inconsistencies)/total_nbr_unique_spawn_points*100)

    if args.merge:
        print "%s (spawn point, time) combinations" % len(merged_spawns)
        with open(args.out, "w") as out:
            json.dump(merged_spawns, out)
        print "Wrote merged spawns to %s" % out.name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", metavar="spawns.json", nargs="+")
    parser.add_argument("-m", "--merge",
      dest="merge", action="store_true",
      help="Will produce a single file with all spawn points from the input fields")
    parser.add_argument("-o", "--out",  type=str,
      help="Output file to write when mergin")
    parser.add_argument("-ft", dest="filetype",
      help="Type of file to merge (spawns, gyms, stops)")
    parser.add_argument("--fi",
      dest="show_file_occurrence_inconsistencies", action="store_true",
      help="Print all spawn points that didn't occur in all input files")
    parser.add_argument("--fti",
      dest="show_file_times_inconsistencies", action="store_true",
      help="Print all spawn points that have different time stamps in different files")
    parser.add_argument("--mt",
      dest="show_multiple_times", action="store_true",
      help="Print all spawn point with more that one spawn time")
    parser.set_defaults(filetype=u'spawns')
    parser.set_defaults(merge=False)
    parser.set_defaults(show_file_occurrence_inconsistencies=False)
    parser.set_defaults(show_file_times_inconsistencies=False)
    parser.set_defaults(show_multiple_times=False)
    parser.set_defaults(out="merged_spawns.json")
    args = parser.parse_args()

    files = [open(f, "r") for f in args.files]
    data = [[add_filename(d, f.name) for d in json.load(f)] for f in files]
    for f in files:
        f.close()

    if args.filetype == 'gyms':
        merge_gyms(data, files, args)
    elif args.filetype == 'stops':
        merge_stops(data, files, args)
    else:
        merge_spawns(data, files, args)
