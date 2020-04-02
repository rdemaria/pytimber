import os
import getpass
import logging
import six

import numpy as np

import cmmnbuild_dep_manager

from .check_kerberos import check_kerberos


user_home = os.environ["HOME"]
nxcals_home = os.path.join(user_home, ".nxcals")
keytab = os.path.join(nxcals_home, "keytab")
certs = os.path.join(nxcals_home, "nxcals_cacerts")
username = getpass.getuser()


def schema2dtype(schema):
    dtype = []
    for field in schema.fields():
        ftype = field.dataType().toString()
        fname = field.name()
        if ftype == "StringType":
            dtype.append((fname, "U200"))
        elif ftype == "DoubleType":
            dtype.append((fname, "float64"))
        elif ftype == "LongType":
            dtype.append((fname, "int64"))
        elif ftype == "BooleanType":
            dtype.append((fname, "bool"))
        else:
            print(fname, ftype)
            dtype.append((fname, "object"))
    return np.dtype(dtype)


class NXCals(object):
    @staticmethod
    def rows2array(rows):
        dtype = schema2dtype(rows[0].schema())
        print(dtype)
        return np.fromiter(
            (tuple(row.values()) for row in rows), dtype=dtype, count=len(rows)
        )

    @staticmethod
    def rows2pandas(rows):
        import pandas as pd

        names = list(rows[0].schema().names())
        data = (row.values() for row in rows)
        df = pd.DataFrame.from_records(data, columns=names, nrows=len(rows))
        for idx in "nxcals_timestamp", "timestamp", "acqStamp":
            if idx in names:
                df.set_index(idx)
            break
        return df

    @staticmethod
    def create_certs():
        print(f"Creating {certs}")
        import urllib.request

        url = "https://cafiles.cern.ch/cafiles/certificates/CERN%20Grid%20Certification%20Authority.crt"
        urllib.request.urlretrieve(url, filename="tmpcert")
        cmd = f"keytool -import -alias cerngridcertificationauthority -file tmpcert -keystore {certs} -storepass nxcals -noprompt"
        print(cmd)
        os.system(cmd)
        os.unlink("tmpcert")

    @staticmethod
    def create_keytab():
        if not os.path.isdir(nxcals_home):
            os.mkdir(nxcals_home)
        print(
            f"""Please use `kutil` to create a keytab using the following instruction
ktutil\n
ktutil: add_entry -password -p {username}@CERN.CH -k 1 -e arcfour-hmac-md5
ktutil: wkt {keytab}
ktutil: exit\n
kdestroy && kinit -f -r 5d -kt {keytab} {username}
klist
        """
        )

    def __init__(
        self, user=username, keytab=keytab, certs=certs, loglevel=logging.ERROR
    ):
        """
        Needs
           user: default user name
           keytab: default $HOME/.nxcals/keytab
           certs: default $HOME/.nxcals/nxcals_cacerts
        """

        check_kerberos()


        # Configure logging
        logging.basicConfig()
        self._log = logging.getLogger(__name__)
        if loglevel is not None:
            self._log.setLevel(loglevel)

        # Setup keytab and certs
        self._keytab = None

        if os.path.isfile(keytab):
            self._keytab = keytab
        #else:
        #    try:
        #        NXCals.create_keytab()
        #    except Exception as ex:
        #        print(ex)
        #        raise ValueError(f"Keytab file {keytab} could not be created")

        self._certs = None
        if os.path.isfile(certs):
            self._certs = certs
        #else:
        #    try:
        #        NXCals.create_certs()
        #    except Exception as ex:
        #        print(ex)
        #        raise ValueError(
        #            f"Certificate file {certs} could not be created"
        #        )

        self._user = user

        # Start JVM and set basic hook
        self._mgr = cmmnbuild_dep_manager.Manager("pytimber", loglevel)
        self._jpype = self._mgr.start_jpype_jvm()
        self._org = self._jpype.JPackage("org")
        self._cern = self._jpype.JPackage("cern")
        self._java = self._jpype.java
        self._System = self._java.lang.System

        # spark config
        try:
            self.spark = self._get_spark()
        except self._jpype.JavaException as ex:
            print(ex.message())
            print(ex.stacktrace())
            raise ex

        # nxcals shortcuts
        self._builders = self._cern.nxcals.api.extraction.data.builders
        self._Variables = (
            self._cern.nxcals.api.extraction.metadata.queries.Variables
        )
        self._ServiceClientFactory = (
            self._cern.nxcals.api.extraction.metadata.ServiceClientFactory
        )

        # pytimber helpers
        self._SparkDataFrameConversions = (
            self._org.pytimber.utils.SparkDataFrameConversions
        )

        # nxcals services
        try:
            self._variableService = (
                self._ServiceClientFactory.createVariableService()
            )
            self._entityService = (
                self._ServiceClientFactory.createEntityService()
            )
        except TypeError:
            print("Possible problems with kerberos. Checking with keylist")
            os.system("klist")

        # self._systemService=self._ServiceClientFactory.createSystemService()

    # @property
    # def DevicePropertyQuery(self):
    #    return self.builders.DevicePropertyQuery.builder(self.spark)

    # @property
    # def VariableQuery(self):
    #    return self.builders.VariableQuery.builder(self.spark)

    # @property
    # def KeyValuesQuery(self):
    #    return self.builders.KeyValuesQuery.builder(self.spark)

    def _get_spark(self):
        self._System.setProperty("spring.main.web-application-type", "none")
        if self._certs is not None:
            self._System.setProperty("javax.net.ssl.trustStore", self._certs)
            self._System.setProperty(
                "javax.net.ssl.trustStorePassword", "nxcals"
            )

        if self._user is not None:
            self._System.setProperty("kerberos.principal", self._user)

        if self._keytab is not None:
            self._System.setProperty("kerberos.keytab", self._keytab)

        self._System.setProperty(
            "service.url",
            "https://cs-ccr-nxcals6.cern.ch:19093,https://cs-ccr-nxcals7.cern.ch:19093,https://cs-ccr-nxcals8.cern.ch:19093",
        )

        self._NxcalsSparkSession = self._org.pytimber.utils.NxcalsSparkSession
        self._NxcalsSparkSession.setVerboseLogging(False)
        return self._NxcalsSparkSession.sparkSession()

    def searchVariable(self, pattern, system="CMW"):
        query = (
            self._Variables.suchThat()
            .systemName()
            .eq(system)
            .and_()
            .variableName()
            .like(pattern)
        )
        out = [
            k.getVariableName() for k in self._variableService.findAll(query)
        ]
        return sorted(out)

    @property
    def DataQuery(self):
        return self._builders.DataQuery.builder(self.spark)

    def getVariablesList(self, pattern_or_list, system="CMW"):
        if isinstance(pattern_or_list, six.string_types):
            return self.searchVariable(pattern_or_list, system=system)
        elif isinstance(pattern_or_list, (list, tuple)):
            return pattern_or_list
        else:
            return None

    def get(self, pattern_or_list, t1, t2, system="CMW", output="data"):
        variables = self.getVariablesList(pattern_or_list, system=system)
        out = {}
        for variable in variables:
            out[variable] = self.getVariable(
                variable, t1, t2, system=system, output=output
            )
        return out

    def getVariable(self, variable, t1, t2, system="CMW", output="data"):
        ds = (
            self.DataQuery.byVariables()
            .system(system)
            .startTime(t1)
            .endTime(t2)
            .variable(variable)
            .buildDataset()
        )
        if output == "spark":
            return ds
        elif output == "data":
            return self.processVariable(ds)

    def processVariable(self, ds):
        data = (
            ds.sort("nxcals_timestamp")
            .select("nxcals_timestamp", "nxcals_value")
            .na()
            .drop()
        )
        ts_type = data.dtypes()[0]._2()
        val_type = data.dtypes()[1]._2()
        ts = np.array(self._SparkDataFrameConversions.extractDoubleColumn(
            data, "nxcals_timestamp"
        ))
        if val_type == "FloatType" or val_type == "DoubleType":
            val = np.array(self._SparkDataFrameConversions.extractDoubleColumn(
                data, "nxcals_value"
            ))
        elif val_type == "LongType":
            val = np.array(self._SparkDataFrameConversions.extractLongColumn(
                data, "nxcals_value"
            ))
        else:
            val = np.array(self._SparkDataFrameConversions.extractColumn(
                data, "nxcals_value"
            ))
        return ts[:] / 1e9, val

    def searchEntity(self, pattern):
        out = []
        for k in self._entityService.findByKeyValuesLike(pattern):
            d = k.entityKeyValues
            try:
                data = (d["variable_name"], d["device"], d["property"])
            except (NameError, TypeError) as ex:
                print(ex)
                data = k
            out.append(data)
        return out

    def searchDevice(self, pattern):
        out = []
        for k in self._entityService.findByKeyValuesLike(pattern):
            d = k.entityKeyValues
            if d["device"] is not None:
                out.append((d["device"], d["property"]))
        return out
