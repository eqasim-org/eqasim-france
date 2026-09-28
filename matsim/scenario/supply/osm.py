import os.path

import matsim.runtime.pt2matsim as pt2matsim

def configure(context):
    pt2matsim.configure(context)
    context.stage("matsim.runtime.pt2matsim")
    
    context.stage("data.osm.cleaned")

    context.config("export_detailed_network", False)
    context.config("crs", "EPSG:2154")

def execute(context):
    osm_path = "{}/output.osm.gz".format(context.path("data.osm.cleaned"))

    pt2matsim.run(context, "org.matsim.pt2matsim.run.CreateDefaultOsmConfig", 
        arguments=["config_template.xml"]
    )

    with open("%s/config_template.xml" % context.path()) as f_read:
        content = f_read.read()

        content = content.replace(
            '<param name="osmFile" value="null" />',
            '<param name="osmFile" value="{}" />'.format(osm_path)
        )

        content = content.replace(
            '<param name="writeCRS" value="false" />',
            '<param name="writeCRS" value="true" />'
        )

        content = content.replace(
            '<param name="outputCoordinateSystem" value="null" />',
            '<param name="outputCoordinateSystem" value="{}" />'.format(context.config("crs"))
        )

        content = content.replace(
            '<param name="outputNetworkFile" value="null" />',
            '<param name="outputNetworkFile" value="network.xml.gz" />'
        )

        if context.config("export_detailed_network"):
            content = content.replace(
                '<param name="outputDetailedLinkGeometryFile" value="null" />',
                '<param name="outputDetailedLinkGeometryFile" value="detailed_network.csv" />',
            )

        content = content.replace(
            '</module>',
            """
                <parameterset type="routableSubnetwork">
                    <param name="allowedTransportModes" value="car" />
                    <param name="subnetworkMode" value="car_passenger" />
                </parameterset>
            </module>
            """
        )

        with open("%s/config.xml" % context.path(), "w+") as f_write:
            f_write.write(content)

    pt2matsim.run(context, "org.matsim.pt2matsim.run.Osm2MultimodalNetwork", 
        arguments=["config.xml"]
    )

    assert(os.path.exists("%s/network.xml.gz" % context.path()))
    return "network.xml.gz"
