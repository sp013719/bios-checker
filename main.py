__author__ = 'sp013719'

import csv
import sys
from connection.ssh import Ssh

RESULT_FILE_NAME = 'result.csv'


def quality_assurance(file_name, account, password):
    servers = get_server_list(file_name)

    with open(RESULT_FILE_NAME, 'w') as csv_file:
        headers = ['SN', 'DRAC', 'FQDN', 'ServerType', 'BootSeq', 'HddSeq', 'InternalSD', 'Note']
        writer = csv.DictWriter(csv_file, delimiter=',', lineterminator='\n',  fieldnames=headers)
        writer.writeheader()

        server_amount = len(servers)
        for idx, server in enumerate(servers, 1):
            print('Checking the server [%s] ..... (%s/%s)' % (server['fqdn'], idx, server_amount))
            boot_seq, hdd_seq, internal_sd = check_bios_config(server, account, password)

            result = dict()
            result['SN'] = server['sn']
            result['DRAC'] = server['drac']
            result['FQDN'] = server['fqdn']
            result['ServerType'] = server['type']

            if not boot_seq or not hdd_seq or not internal_sd:
                result['Note'] = 'Inaccessible'
            else:
                result['BootSeq'] = boot_seq
                result['HddSeq'] = hdd_seq
                result['InternalSD'] = internal_sd

            writer.writerow(result)
            print('Checking the server [%s] complete (%s/%s)' % (server['fqdn'], idx, server_amount))


def get_server_list(file_name):
    servers = []

    with open(file_name, 'r') as f:
        for row in csv.DictReader(f):
            server = dict()
            server['sn'] = row['SN']
            server['drac'] = row['DRAC']
            server['fqdn'] = row['FQDN']
            server['type'] = 'Hypervisor' if server['fqdn'].find('esx') > -1 else 'Standalone'
            servers.append(server)

    return servers


def check_bios_config(server, account, password):
    if not server:
        print('server is None')
        return None, None, None

    ssh = Ssh(server['drac'], account, password, port=22)
    opened = ssh.open()

    if opened:
        raw_boot_seq = ssh.execute('racadm get BIOS.BiosBootSettings.BootSeq')
        boot_seq = raw_boot_seq if len(raw_boot_seq.split('=')) < 3 else (raw_boot_seq.split('=')[2]).replace(',', '\r\n')
        raw_hdd_seq = ssh.execute('racadm get BIOS.BiosBootSettings.HddSeq')
        hdd_seq = raw_boot_seq if len(raw_hdd_seq.split('=')) < 3 else (raw_hdd_seq.split('=')[2]).replace(',', '\r\n')
        raw_internal_sd = ssh.execute('racadm get BIOS.IntegratedDevices.InternalSdCard')
        internal_sd = raw_internal_sd if len(raw_internal_sd.split('=')) < 3 else (raw_internal_sd.split('=')[2])
        ssh.close()
        return boot_seq, hdd_seq, internal_sd
    else:
        return None, None, None


if __name__ == '__main__':
    assert len(sys.argv) == 4
    file = sys.argv[1]
    drac_account = sys.argv[2]
    drac_password = sys.argv[3]
    quality_assurance(file, drac_account, drac_password)
