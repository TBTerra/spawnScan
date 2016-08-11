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

parser = argparse.ArgumentParser(
  description=__doc__)
parser.add_argument("files", metavar="spawns.json", nargs="+")
parser.add_argument("-m", "--merge",
  dest="merge", action="store_true",
  help="Will produce a single file with all spawn points from the input fiels")
parser.add_argument("-o", "--out",  type=str,
  help="Output file to write when mergin")
parser.add_argument("--fi",
  dest="show_file_occurrence_inconsistencies", action="store_true",
  help="Print all spawn points that didn't occur in all input files")
parser.add_argument("--fti",
  dest="show_file_times_inconsistencies", action="store_true",
  help="Print all spawn points that have different time stamps in different files")
parser.add_argument("--mt",
  dest="show_multiple_times", action="store_true",
  help="Print all spawn point with more that one spawn time")
parser.set_defaults(merge=False)
parser.set_defaults(show_file_occurrence_inconsistencies=False)
parser.set_defaults(show_file_times_inconsistencies=False)
parser.set_defaults(show_multiple_times=False)
parser.set_defaults(out="merged_spawns.json")
args = parser.parse_args()

def add_filename(spawn_point, filename):
  spawn_point["filename"] = filename
  return spawn_point

def print_filetimes(filetimes):
  for fn, ts in filetimes.iteritems():
    print "  %s: [%s]" % (fn, ", ".join([str(x) for x in sorted(ts)]))

files = [open(f, "r") for f in args.files]
data = [[add_filename(d, f.name) for d in json.load(f)] for f in files]
for f in files:
  f.close()

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
