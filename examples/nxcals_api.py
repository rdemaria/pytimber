import cmmnbuild_dep_manager


mgr = cmmnbuild_dep_manager.Manager()

jpype = mgr.start_jpype_jvm()

org = jpype.JPackage("org")
cern = jpype.JPackage("cern")
java = jpype.java
System = java.lang.System


import pytimber

nxcals = pytimber.NXCals()


nxcals.searchVariable("SPS%")
