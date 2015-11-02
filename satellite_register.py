__author__ = 'scott.a.clark'

import satellite
import subprocess
from sys import exit


def do_satellite_register():
    u = ("Usage: %prog [options] capsule_fqdn\n"
         "capsule_fqdn is the fully-qualified domain of the Satellite Capsule endpoint to which you are registering.\n"
         "It may be the embedded Capsule within the Satellite master or any standalone Capsule in your environment.")

    parser = satellite.SatelliteOptParse(u)
    (clo, cla) = parser.parse_args()

    try:
        sy = satellite.SatelliteYum()
        me = satellite.CurrentHost(clo, cla[0])
        # Check the input with the user before proceeding if they have not used the -y option
        if not clo.yes:
            satellite.print_confirmation(me)

        # Proceed with script, noting short-circuits
        if not clo.skip_update_rhsm:
            sy.get_latest("subscription-manager")

        if not clo.skip_rhn_clean:
            sy.clean_rhn_classic()

        if not clo.skip_katelloca:
            # sy.localinstall_katelloca(me.master)
            sy.localinstall(rpm="katello-ca-consumer-latest.noarch.rpm", remotedir="pub", srcdir=clo.tmpdir,
                            remotehost=me.master, ssl=clo.ssl)

        if not clo.skip_register:
            me.register()

        if not clo.skip_install:
            sy.install_sat6()
            subprocess.call("/usr/sbin/katello-package-upload")

        if not clo.skip_puppet:
            satellite.configure_puppet(me.master)
            # First run generates certificate
            satellite.puppet_run()
            # If not autosigned, maybe additional code required here?
            # Second run validates certificate
            satellite.puppet_run()
    except satellite.CurrentHostException, che:
        print che
        exit(69)  # 69.pem is the certificate file for RHEL
    except satellite.SatellitePuppetException, spe:
        print spe
        exit(2)
    except Exception, e:
        # Catch-all Exception Handling
        exception_type = e.__class__.__name__
        if exception_type == "SystemExit":
            exit()
        else:
            print " EXCEPTION(" + exception_type + "): " + str(e)
            exit(-1)


# Make this "runnable"
if __name__ == "__main__":
    do_satellite_register()
