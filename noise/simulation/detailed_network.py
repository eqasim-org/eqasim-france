from synpp import ConfigurationContext, ExecuteContext

import pandas as pd
import gzip
import xml.etree.ElementTree as ET


def configure(context: ConfigurationContext):
    context.stage("matsim.simulation.cutter.cut")

    context.config("export_detailed_network")
    context.config("cutter_name", "cutter")

    context.config("output_path")
    context.config("output_prefix")


def execute(context: ExecuteContext):

    df_detailed_network = pd.read_csv(
        "%s/%s" % (
            context.config("output_path"),
            "%sdetailed_network.csv" % context.config("output_prefix"),
        ),
    )

    cutter_name = context.config("cutter_name")

    network_path = "%s/%s/%s_network.xml.gz" % (
        context.config("output_path"),
        cutter_name,
        cutter_name,
    )


    # Read the gziped XML file
    with gzip.open(network_path, 'rt', encoding='utf-8') as f:
        tree = ET.parse(f)

    # Extract all distinct osm:way:id attributes
    root = tree.getroot()
    way_ids = []

    for link in root.findall(".//link"):
        way_ids.append(link.get("id"))
        # attributes = link.find("attributes")
        # if attributes is not None:
        #     for attribute in attributes.findall("attribute"):
        #         if attribute.get("name") == "osm:way:id":
        #             osm_way_ids.append(attribute.text)

    # Convert the set to a list
    # osm_way_ids = list(osm_way_ids)

    df_detailed_network = df_detailed_network[
        df_detailed_network["LinkId"].astype(str).isin(way_ids)
    ]

    # Save the filtered DataFrame to a CSV file
    df_detailed_network.to_csv(
        "%s/%s/%s_detailed_network.csv" % (
            context.config("output_path"),
            cutter_name,
            cutter_name,
        ),
        index=False,
    )

    return "%s_detailed_network.csv" % (
        cutter_name,
    )

def validate(context: ExecuteContext):
    if not context.config("export_detailed_network"):
        raise ValueError(
            "Export detailed network is not enabled, cannot run a NoiseModelling simulation."
        )
