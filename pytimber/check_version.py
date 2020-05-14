import cmmnbuild_dep_manager
import urllib


def check_installed_version(mgr, name):
    jar = filter(lambda j: name in j, mgr.jars())
    jar = list(jar)[0]
    version = list(map(int, jar.split("-")[-1].split(".")[:-1]))
    return version


def check_nxcals_online_version():
    url = "https://gitlab.cern.ch/scripting-tools/pytimber/-/raw/master/nxcalx_api_version"
    response = urllib.request.urlopen(url).read().decode().strip()
    version = list(map(int, response.split(".")))
    return version


def check_nxcals_version():
    mgr = cmmnbuild_dep_manager.Manager()
    installed = check_installed_version(mgr, "nxcals-extraction-api")
    proposed = check_nxcals_online_version()
    if proposed > installed:
        mgr.resolve()
