import cmmnbuild_dep_manager

def check_nxcals_version():
    mgr=cmmnbuild_dep_manager.Manager()
    api=filter(lambda j: "nxcals-extraction-api" in j, mgr.jars())
    api=list(api)[0]
    version=list(map(int,api.split('-')[-1].split('.')[:-1]))
    return version


check_nxcals_version()

