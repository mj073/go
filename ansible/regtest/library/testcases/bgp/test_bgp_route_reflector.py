#!/usr/bin/python
""" Test/Verify BGP Routes """

#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#

import shlex

from collections import OrderedDict

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: test_bgp_route_reflector
author: Platina Systems
short_description: Module to test and verify bgp configurations.
description:
    Module to test and verify bgp configurations and log the same.
options:
    switch_name:
      description:
        - Name of the switch on which tests will be performed.
      required: False
      type: str
    leaf_network_list:
      description:
        - Comma separated list of all leaf bgp networks.
      required: False
      type: str
    spine_list:
      description:
        - List of all spine switches.
      required: False
      type: list
      default: []
    config_file:
      description:
        - BGP config which have been added.
      required: False
      type: str
    package_name:
      description:
        - Name of the package installed (e.g. quagga/frr/bird).
      required: False
      type: str
    hash_name:
      description:
        - Name of the hash in which to store the result in redis.
      required: False
      type: str
    log_dir_path:
      description:
        - Path to log directory where logs will be stored.
      required: False
      type: str
"""

EXAMPLES = """
- name: Verify bgp peering routes
  test_bgp_route_reflector:
    switch_name: "{{ inventory_hostname }}"
    hash_name: "{{ hostvars['server_emulator']['hash_name'] }}"
    log_dir_path: "{{ log_dir_path }}"
"""

RETURN = """
hash_dict:
  description: Dictionary containing key value pairs to store in hash.
  returned: always
  type: dict
"""

RESULT_STATUS = True
HASH_DICT = OrderedDict()


def run_cli(module, cli):
    """
    Method to execute the cli command on the target node(s) and
    returns the output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output/Error or None depending upon the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out.rstrip()
    elif err:
        return err.rstrip()
    else:
        return None


def execute_commands(module, cmd):
    """
    Method to execute given commands and return the output.
    :param module: The Ansible module to fetch input parameters.
    :param cmd: Command to execute.
    :return: Output of the commands.
    """
    global HASH_DICT

    if 'service' in cmd and 'restart' in cmd:
        out = None
    else:
        out = run_cli(module, cmd)

    # Store command prefixed with exec time as key and
    # command output as value in the hash dictionary
    exec_time = run_cli(module, 'date +%Y%m%d%T')
    key = '{0} {1} {2}'.format(module.params['switch_name'], exec_time, cmd)
    HASH_DICT[key] = out

    return out


def verify_rr_client(module, switch_name, network):
    """
    Method to verify RR client.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: Name of the switch.
    :param network: Network address against which RR request to verify.
    :return: Failure summary if any.
    """
    global RESULT_STATUS
    failure_summary = ''

    cmd = "vtysh -c 'sh ip bgp {}'".format(network)
    out = execute_commands(module, cmd)

    # For errors, update the result status to False
    if out is None or 'error' in out:
        RESULT_STATUS = False
        failure_summary += 'On Switch {} '.format(switch_name)
        failure_summary += 'output of command {} is None\n'.format(cmd)
    else:
        if 'Received from a RR-client' not in out:
            RESULT_STATUS = False
            failure_summary += 'On Switch {} '.format(switch_name)
            failure_summary += 'output of command {} '.format(cmd)
            failure_summary += 'did not display Received from a RR-client '
            failure_summary += 'for network {}\n'.format(network)

    return failure_summary


def verify_advertised_routes(module, switch_name, network, ip):
    """
    Method to verify advertised routes.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: Name of the switch.
    :param network: Network address.
    :param ip: Interface address.
    :return: Failure summary if any.
    """
    global RESULT_STATUS
    failure_summary = ''

    cmd = "vtysh -c 'sh ip bgp neighbors {} advertised-routes'".format(ip)
    out = execute_commands(module, cmd)

    # For errors, update the result status to False
    if out is None or 'error' in out:
        RESULT_STATUS = False
        failure_summary += 'On Switch {} '.format(switch_name)
        failure_summary += 'output of command {} is None\n'.format(cmd)
    else:
        if network not in out:
            RESULT_STATUS = False
            failure_summary += 'On Switch {} '.format(switch_name)
            failure_summary += 'output of command {} '.format(cmd)
            failure_summary += 'did not display network {}\n'.format(network)

    return failure_summary


def verify_bgp_routes(module):
    """
    Method to verify bgp routes.
    :param module: The Ansible module to fetch input parameters.
    """
    global RESULT_STATUS, HASH_DICT
    failure_summary = ''
    self_network = ''
    switch_name = module.params['switch_name']
    spine_list = module.params['spine_list']
    package_name = module.params['package_name']
    
    # Get the current/running configurations
    execute_commands(module, "vtysh -c 'sh running-config'")

    # Restart and check package status
    execute_commands(module, 'service {} restart'.format(package_name))
    execute_commands(module, 'service {} status'.format(package_name))

    is_spine = True if switch_name in spine_list else False
    if is_spine:
        if spine_list.index(switch_name) == 0:
            # Verify Received from RR client
            for network in module.params['leaf_network_list'].split(','):
                network = network.split('/')[0]
                failure_summary += verify_rr_client(module, switch_name,
                                                    network)

            # Verify advertised routes
            for line in module.params['config_file'].splitlines():
                line = line.strip()
                if line.startswith('network'):
                    self_network = (line.split()[1]).split('/')[0]

                if line.startswith('neighbor') and 'remote-as' not in line:
                    ip = line.split()[1]
                    failure_summary += verify_advertised_routes(
                        module, switch_name, self_network, ip
                    )

    HASH_DICT['result.detail'] = failure_summary

    # Get the GOES status info
    execute_commands(module, 'goes status')


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            switch_name=dict(required=False, type='str'),
            leaf_network_list=dict(required=False, type='str'),
            spine_list=dict(required=False, type='list', default=[]),
            config_file=dict(required=False, type='str'),
            package_name=dict(required=False, type='str'),
            hash_name=dict(required=False, type='str'),
            log_dir_path=dict(required=False, type='str'),
        )
    )

    global HASH_DICT, RESULT_STATUS

    verify_bgp_routes(module)

    # Calculate the entire test result
    HASH_DICT['result.status'] = 'Passed' if RESULT_STATUS else 'Failed'

    # Create a log file
    log_file_path = module.params['log_dir_path']
    log_file_path += '/{}.log'.format(module.params['hash_name'])
    log_file = open(log_file_path, 'w')
    for key, value in HASH_DICT.iteritems():
        log_file.write(key)
        log_file.write('\n')
        log_file.write(str(value))
        log_file.write('\n')
        log_file.write('\n')

    log_file.close()

    # Exit the module and return the required JSON.
    module.exit_json(
        hash_dict=HASH_DICT,
        log_file_path=log_file_path
    )

if __name__ == '__main__':
    main()

