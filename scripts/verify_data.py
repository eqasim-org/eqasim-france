import requests
import time
import yaml

# The goal of this script is to verify the availability of the data 
# that is needed to set up the pipeline

sleep_time = 5 # seconds
timeout = 30 # seconds
retries = 3

# We only test for a selection (IDF)
departments = ("75", "77", "78", "91", "92", "93", "94", "95")

class Report:
    def __init__(self):
        self.sources = []

    def register(self, name, url):
        self.sources.append({ "name": name, "url": url })

    def validate(self):
        failed = []

        with requests.Session() as session:
            session.headers.update({ "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0" })
            for index, source in enumerate(self.sources):
                print("[{}/{}] Checking {} ...".format(index + 1, len(self.sources), source["name"]))
                
                retry = 0
                success = False

                while not success and retry < retries:
                    try:
                        response = session.head(source["url"], timeout = timeout, allow_redirects = True)
                        source["status"] = response.status_code
                        success = True
                    except TimeoutError:
                        source["status"] = "timeout"
                    except Exception as e:
                        source["status"] = "error"
                        print(e)

                    retry += 1
                    print("  Status {} (retry {}/{})".format(source["status"], retry, retries))
                    
                    time.sleep(sleep_time)

                if source["status"] != 200:
                    failed.append(source["name"])
        
        print("Done.")
        print("Missing: ", len(failed))
        print(failed)

        return len(failed) == 0

report = Report()

with open("data/registry.yml") as f:
    registry = yaml.load(f, yaml.SafeLoader)

    for name, source in registry["registry"].items():
        for file_index, file in enumerate(source["files"]):
            title = source["description"]

            if "description" in file:
                title += " / " + file["description"]

            elif len(source["files"]) > 1:
                title += " / " + "{}/{}".format(file_index + 1, len(source["files"]))

            if not file.get("per_department", False):
                report.register(title, file["url"])
            else:
                for department in departments:
                    department_title = title + " / " + department
                    url = file["url"].format(department = department)
                    report.register(department_title, url)

with open("data/geofabrik.yml") as f:
    registry = yaml.load(f, yaml.SafeLoader)

    template = registry["geofabrik"]["url"]
    version = registry["geofabrik"]["version"]

    selection = set()
    for name, coverage in registry["geofabrik"]["coverage"].items():
        coverage = set(coverage) & set(departments)

        if len(coverage) > 0:
            selection.add(name)
    
    for name in selection:
        title = "Geofabrik: {} @ {}".format(name, version)
        url = template.format(id = name, version = version)
        report.register(title, url)

exit(0 if report.validate() else 1)
