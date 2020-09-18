import cmmnbuild_dep_manager
import jpype
import  jpype.imports

mgr=cmmnbuild_dep_manager.Manager()
mgr.start_jpype_jvm()
jpype.imports.registerDomain("cern")

from java.util import HashMap

from cern.nxcals.common.utils.SparkUtils \
        import createSparkSession, createSparkConf
from cern.nxcals.api.config import SparkProperties
from cern.nxcals.api.extraction.data.builders import DataQuery

System = jpype.java.lang.System
System.setProperty(
                "service.url",
                "https://cs-ccr-nxcals6.cern.ch:19093,https://cs-ccr-nxcals7.cern.ch:19093,https://cs-ccr-nxcals8.cern.ch:19093"
)


props={"spark.executor.memory":"2G",
       "spark.executor.cores":"10",
       "spark.yarn.appMasterEnv.JAVA_HOME":"/var/nxcals/jdk1.8.0_121",
       "spark.executorEnv.JAVA_HOME":"/var/nxcals/jdk1.8.0_121",
       "spark.yarn.jars":"hdfs:////project/nxcals/lib/spark-2.4.0/*.jar",
       "spark.yarn.am.extraLibraryPath":"/usr/lib/hadoop/lib/native",
       "spark.executor.extraLibraryPath":"/usr/lib/hadoop/lib/native",
       "spark.yarn.historyServer.address":"ithdp1001.cern.ch:18080",
       "spark.yarn.access.hadoopFileSystems":"nxcals",
       "spark.sql.caseSensitive":"true"}

spark_properties=SparkProperties()
spark_properties.setAppName("PYTIMBER3")
spark_properties.setMasterType("yarn")
spark_properties.setProperties(props)
spark_conf=createSparkConf(spark_properties)
spark=createSparkSession(spark_conf)


ds=( DataQuery.builder(spark).byEntities()
    .system("CMW")
    .startTime("2018-04-29 00:00:00.000")
    .endTime("2018-04-30 00:00:00.000")
    .entity()
    .keyValue("device", "LHC.LUMISCAN.DATA")
    .keyValue("property", "CrossingAngleIP1")
    .buildDataset()
)

rows = ds.collect()

print(rows)

