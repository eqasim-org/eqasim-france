import collections
import gzip
import xml.etree.ElementTree as ET

"""
Merges MATSim transit routes that only differ in their timing.

pt2matsim creates one transit route per distinct timing pattern of a line, so
that many routes have only one or a few departures. SwissRailRaptor works on
route stops and transfers between them, whose number grows with the number of
routes, which makes public transport routing (mode choice, simulation)
memory-bound and slow.

Routes of the same line with the same mode, description, attributes, stops
(and their flags) and network path are merged if their arrival and departure
offsets differ by at most a tolerance at every stop. A merged route keeps the
offsets of its member with the most departures; the other departures keep their
departure time but follow these offsets, so that their times at every stop
shift by at most the tolerance.

Routes involved in chained departures are never merged.
"""

OFFSETS = ("arrivalOffset", "departureOffset")

DOCTYPE = '<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v2.dtd">'

def parse_time(value):
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

def route_signature(route):
    """ Returns the merge key of a route and its offsets in seconds """
    stops = route.find("routeProfile").findall("stop")

    stop_key = tuple(
        tuple(sorted((key, value) for key, value in stop.attrib.items() if not key in OFFSETS))
        + tuple(stop.get(offset) is None for offset in OFFSETS)
        for stop in stops
    )

    network_route = route.find("route")
    links = () if network_route is None else tuple(link.get("refId") for link in network_route.findall("link"))

    offsets = [
        parse_time(stop.get(offset))
        for stop in stops for offset in OFFSETS
        if stop.get(offset) is not None
    ]

    attributes = route.find("attributes")
    attributes = None if attributes is None else ET.tostring(attributes)

    return (route.findtext("transportMode"), route.findtext("description"), attributes, stop_key, links), offsets

def chained_routes(root):
    """ Returns the (line, route) identifiers involved in chained departures """
    routes = set()

    for line in root.findall("transitLine"):
        for route in line.findall("transitRoute"):
            for chained in route.iter("chainedDeparture"):
                routes.add((line.get("id"), route.get("id")))
                routes.add((chained.get("toTransitLine", line.get("id")), chained.get("toTransitRoute")))

    return routes

def max_deviation(first, second):
    return max((abs(a - b) for a, b in zip(first, second)), default = 0.0)

def merge_schedule(root, tolerance):
    """ Merges the routes of the parsed schedule in place and returns statistics """
    excluded = chained_routes(root)
    statistics = collections.Counter()
    shifts = []

    for line in root.findall("transitLine"):
        groups = collections.defaultdict(list)

        for route in line.findall("transitRoute"):
            key, offsets = route_signature(route)

            if (line.get("id"), route.get("id")) in excluded:
                key = (key, route.get("id"))

            departures = len(route.find("departures").findall("departure"))
            groups[key].append((departures, route, offsets))

        for members in groups.values():
            # The route with the most departures defines the offsets of its cluster
            members.sort(key = lambda member: -member[0])
            clusters = []

            for departures, route, offsets in members:
                cluster, deviation = None, None

                for candidate in clusters:
                    deviation = max_deviation(candidate[1], offsets)

                    if deviation <= tolerance:
                        cluster = candidate
                        break

                if cluster is None:
                    clusters.append((route, offsets))
                    continue

                shifts += [deviation] * departures

                target = cluster[0].find("departures")
                identifiers = set(departure.get("id") for departure in target)

                for departure in route.find("departures").findall("departure"):
                    identifier, suffix = departure.get("id"), 1

                    while identifier in identifiers:
                        identifier = "%s_%s" % (route.get("id"), departure.get("id"))
                        identifier += "" if suffix == 1 else "_%d" % suffix
                        suffix += 1

                    departure.set("id", identifier)
                    identifiers.add(identifier)
                    target.append(departure)

                line.remove(route)
                statistics["merged_routes"] += 1

            for route, offsets in clusters:
                target = route.find("departures")
                target[:] = sorted(target, key = lambda departure: parse_time(departure.get("departureTime")))

    routes = [route for line in root.findall("transitLine") for route in line.findall("transitRoute")]
    statistics["routes"] = len(routes)
    statistics["route_stops"] = sum(len(route.find("routeProfile")) for route in routes)
    statistics["shifted_departures"] = sum(1 for shift in shifts if shift > 0)
    statistics["maximum_shift"] = max(shifts, default = 0.0)

    return statistics

def merge_schedule_file(input_path, output_path, tolerance):
    """ Reads a (gzipped) MATSim transit schedule, merges its routes and writes it """
    with gzip.open(input_path) as f:
        tree = ET.parse(f)

    statistics = merge_schedule(tree.getroot(), tolerance)

    ET.indent(tree, space = "\t")

    with gzip.open(output_path, "wt", encoding = "utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n%s\n\n' % DOCTYPE)
        tree.write(f, encoding = "unicode")
        f.write("\n")

    return statistics
