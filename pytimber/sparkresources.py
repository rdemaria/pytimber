from enum import Enum, unique


@unique
class SparkResources(Enum):
    SMALL = ("small", "2G", "10")
    MEDIUM = ("medium", "4G", "20")
    LARGE = ("large", "8G", "20")
    CUSTOM = ("custom", "", "")

    def __init__(self, description, memory, cores):
        self.description = description
        self.memory = memory
        self.cores = cores
        self._props = {}

    @classmethod
    def from_str(cls, name):
        for resource in SparkResources:
            if resource.name == name:
                return resource
        raise ValueError("{} is not a valid SparkResource name".format(name))

    @property
    def properties(self):
        self._props["spark.executor.memory"] = self.memory
        self._props["spark.executor.cores"] = self.cores

        self._props[
            "spark.yarn.appMasterEnv.JAVA_HOME"
        ] = "/var/nxcals/jdk1.8.0_121"
        self._props["park.executorEnv.JAVA_HOME"] = "/var/nxcals/jdk1.8.0_121"

        self._props[
            "spark.yarn.jars"
        ] = "hdfs:////project/nxcals/lib/spark-2.4.0/*.jar"
        self._props[
            "spark.yarn.am.extraLibraryPath"
        ] = "/usr/lib/hadoop/lib/native"
        self._props[
            "spark.executor.extraLibraryPath"
        ] = "/usr/lib/hadoop/lib/native"

        self._props[
            "spark.yarn.historyServer.address"
        ] = "ithdp1001.cern.ch:18080"
        self._props["spark.yarn.access.hadoopFileSystems"] = "nxcals"

        self._props['spark.sql.caseSensitive'] = "true"

        return self._props
