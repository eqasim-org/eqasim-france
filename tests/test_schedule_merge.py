import gzip
import xml.etree.ElementTree as ET

import matsim.scenario.supply.schedule_merge as schedule_merge

def stop(stop_id, arrival, departure):
    return '<stop refId="%s" arrivalOffset="%s" departureOffset="%s" awaitDeparture="true"/>' % (stop_id, arrival, departure)

def route(route_id, stops, departures, links = ("1", "2"), mode = "bus", chained = None):
    departures_xml = "".join(
        '<departure id="%s" departureTime="%s" vehicleRefId="veh_%s_%s">%s</departure>' % (
            departure_id, time, route_id, departure_id,
            "" if chained is None or departure_id != chained[0] else
            '<chainedDeparture toDeparture="%s" toTransitLine="%s" toTransitRoute="%s"/>' % chained[1:])
        for departure_id, time in departures
    )

    return """
        <transitRoute id="%s">
            <transportMode>%s</transportMode>
            <routeProfile>%s</routeProfile>
            <route>%s</route>
            <departures>%s</departures>
        </transitRoute>""" % (route_id, mode, "".join(stops), "".join('<link refId="%s"/>' % link for link in links), departures_xml)

BASE = [stop("A", "00:00:00", "00:00:00"), stop("B", "00:05:00", "00:05:00"), stop("C", "00:10:00", "00:10:00")]
SLOWER = [stop("A", "00:00:00", "00:00:00"), stop("B", "00:06:00", "00:06:00"), stop("C", "00:11:00", "00:11:00")]
MUCH_SLOWER = [stop("A", "00:00:00", "00:00:00"), stop("B", "00:08:00", "00:08:00"), stop("C", "00:15:00", "00:15:00")]
OTHER_STOPS = [stop("A", "00:00:00", "00:00:00"), stop("D", "00:05:00", "00:05:00")]

def schedule(*lines):
    return ET.fromstring("<transitSchedule><transitStops/>%s</transitSchedule>" % "".join(
        '<transitLine id="%s">%s</transitLine>' % (line_id, "".join(routes)) for line_id, routes in lines))

def routes(root):
    return {
        route.get("id"): [departure.get("id") for departure in route.find("departures")]
        for route in root.iter("transitRoute")
    }

def example():
    return schedule(("line", [
        route("dominant", BASE, [("d3", "09:00:00"), ("d1", "07:00:00"), ("d2", "08:00:00")]),
        route("slower", SLOWER, [("d1", "07:30:00")]),
        route("much_slower", MUCH_SLOWER, [("d4", "18:00:00")]),
        route("other_stops", OTHER_STOPS, [("d5", "10:00:00")]),
        route("other_links", BASE, [("d6", "11:00:00")], links = ("1", "3")),
        route("other_mode", BASE, [("d7", "12:00:00")], mode = "tram"),
    ]), ("other_line", [
        route("elsewhere", SLOWER, [("d8", "13:00:00")]),
    ]))

def test_zero_tolerance_keeps_routes():
    root = example()
    before = routes(root)

    statistics = schedule_merge.merge_schedule(root, 0)

    assert statistics["merged_routes"] == 0
    assert set(routes(root)) == set(before)

def test_routes_within_tolerance_are_merged():
    root = example()
    statistics = schedule_merge.merge_schedule(root, 60)

    result = routes(root)

    # one minute slower: merged into the dominant route, departures sorted, clashing id renamed
    assert result["dominant"] == ["d1", "slower_d1", "d2", "d3"]
    assert not "slower" in result

    # beyond the tolerance, other stops, links, mode or line: kept
    assert set(result) == { "dominant", "much_slower", "other_stops", "other_links", "other_mode", "elsewhere" }

    assert statistics["merged_routes"] == 1
    assert statistics["shifted_departures"] == 1
    assert statistics["maximum_shift"] == 60
    assert statistics["routes"] == 6

def test_larger_tolerance_merges_more():
    root = example()
    schedule_merge.merge_schedule(root, 300)

    result = routes(root)

    assert result["dominant"] == ["d1", "slower_d1", "d2", "d3", "d4"]
    assert not "much_slower" in result

def test_merged_route_keeps_dominant_offsets():
    root = schedule(("line", [
        route("few", SLOWER, [("a", "07:00:00")]),
        route("many", BASE, [("b", "08:00:00"), ("c", "09:00:00")]),
    ]))

    schedule_merge.merge_schedule(root, 60)

    remaining = list(root.iter("transitRoute"))
    assert [r.get("id") for r in remaining] == ["many"]
    assert [s.get("arrivalOffset") for s in remaining[0].find("routeProfile")] == ["00:00:00", "00:05:00", "00:10:00"]

def test_chained_departures_are_not_merged():
    root = schedule(("line", [
        route("dominant", BASE, [("d1", "07:00:00"), ("d2", "08:00:00")]),
        route("chained", SLOWER, [("d3", "09:00:00")], chained = ("d3", "d9", "line", "target")),
        route("target", SLOWER, [("d9", "10:00:00")]),
    ]))

    statistics = schedule_merge.merge_schedule(root, 600)

    assert statistics["merged_routes"] == 0
    assert set(routes(root)) == { "dominant", "chained", "target" }

def test_file_roundtrip(tmpdir):
    input_path = str(tmpdir.join("schedule.xml.gz"))
    output_path = str(tmpdir.join("merged.xml.gz"))

    with gzip.open(input_path, "wb") as f:
        f.write(ET.tostring(example()))

    statistics = schedule_merge.merge_schedule_file(input_path, output_path, 60)
    assert statistics["merged_routes"] == 1

    with gzip.open(output_path, "rt", encoding = "utf-8") as f:
        content = f.read()

    assert content.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE transitSchedule')
    assert set(routes(ET.fromstring(content.split("\n", 2)[2]))) == set(routes(example())) - { "slower" }

def test_renamed_departures_stay_unique():
    root = schedule(("line", [
        route("dominant", BASE, [("d1", "07:00:00"), ("slower_d1", "08:00:00"), ("d2", "09:00:00")]),
        route("slower", SLOWER, [("d1", "07:30:00")]),
    ]))

    schedule_merge.merge_schedule(root, 60)

    identifiers = routes(root)["dominant"]
    assert len(identifiers) == len(set(identifiers)) == 4
    assert "slower_d1_2" in identifiers

def test_routes_with_other_attributes_are_kept():
    root = schedule(("line", [
        route("dominant", BASE, [("d1", "07:00:00"), ("d2", "08:00:00")]),
        route("slower", SLOWER, [("d3", "07:30:00")]),
    ]))

    attributes = ET.fromstring('<attributes><attribute name="direction" class="java.lang.String">north</attribute></attributes>')
    root.find("transitLine").findall("transitRoute")[1].insert(0, attributes)

    statistics = schedule_merge.merge_schedule(root, 60)

    assert statistics["merged_routes"] == 0
    assert set(routes(root)) == { "dominant", "slower" }
