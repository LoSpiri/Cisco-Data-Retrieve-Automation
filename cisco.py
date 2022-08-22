from netmiko import ConnectHandler
import pandas as pd
import re
from subprocess import PIPE, Popen
# import getpass

# show cdp neighbors
# {'neighbor': 'bgy1-fc-acc-sw-17-1.amazon.com', 'local_interface': 'Ten 1/0/1', 'capability': 'S I', 'platform': 'C9300-48U', 'neighbor_interface': 'Ten 1/1/1'}

# show lldp neighbors   
# {'neighbor': 'bgy1-fc-agg-t1-a-2.a', 'local_interface': 'Te1/0/34', 'capabilities': 'B,R', 'neighbor_interface': 'Te1/0/17'}

# show ip interface brief
# {'intf': 'Port-channel1', 'ipaddr': '100.101.0.0', 'status': 'up', 'proto': 'up'}

# show vlan 
# {'vlan_id': '708', 'name': 'APCVLAN-708', 'status': 'active', 'interfaces': ['Tu0']}

# show mac address-table vlan 708
# {'destination_address': '2829.862d.18ab', 'type': 'DYNAMIC', 'vlan': '708', 'destination_port': ['Po2']}

# show ip arp MAC ADDRESS
# {'protocol': 'Internet', 'address': '10.161.172.91', 'age': '129', 'mac': '2829.862d.187f', 'type': 'ARPA', 'interface': 'Vlan708'}

def connect_to_cisco(username, password, hostname):

    # Router dictionary for netmiko connection
    cisco_device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'secret': password,
        }
    
    try:
        # Establish SSH connection with switch and router
        net_connect = ConnectHandler(**cisco_device)
    except:
        return 1
    else:
        return net_connect



'''
chiedi beccal se usare una sola funzione invece che 2 togliendo get_AP_info
'''
def get_neighbors_set(net_connect_router, substring_type):                                      
    cdp_neighbors = net_connect_router.send_command('show cdp neighbors', use_textfsm=True)
    switch_set = set()
    for entry in cdp_neighbors:
        if(substring_type in entry['neighbor']):       # qui includo solo gli acc-sw, quando creo switch_df aggiungo subito dis-sw
            # print(entry['neighbor'])
            switch_set.add(entry['neighbor'])
    return switch_set
    

def get_switch_IP(net_connect_general):
    # Retrieve IP of switch from mgmt vlan int. Outputs as 'Internet address is 10.../24'
    switch_ip_raw = net_connect_general.send_command('show interface vlan 700 | include Internet')

    switch_ip_split = switch_ip_raw.split(' ')

    return switch_ip_split[5]


def get_aggregator_IP(idf_number,username,password,agg_hostname):
    net_connect_agg_t1 = connect_to_cisco(username,password,agg_hostname)
    ip_interfaces = net_connect_agg_t1.send_command('show ip interface brief', use_textfsm=True)

    for entry in ip_interfaces:
        if entry['intf'] == 'Port-channel' + str(idf_number):
            return entry['ipaddr']



def get_aggregator_info(idf_number,username,password,net_connect_dis_sw):
    cdp_neighbors = net_connect_dis_sw.send_command('show cdp neighbors', use_textfsm=True)

    agg_count = 0
    agg_df = pd.DataFrame(columns=('Aggregator Name','Interface','IP'))

    for entry in cdp_neighbors:
        if 'agg-t1' in entry['neighbor']:
            agg_df.loc[agg_count] = [entry['neighbor'][:-11],entry['neighbor_interface'], get_aggregator_IP(idf_number,username,password,entry['neighbor'])]
            agg_count += 1
    
    return agg_df


def get_switch_uplinks():
    # Send command to grab interfaces that contain '-->' in description
    # Does not use textfsm, just regex
    switch_uplink_raw = net_connect.send_command('sh int desc | inc -->')

    # Regex to remove 'up'
    switch_uplink_rmup = re.sub('<*.?up', '', switch_uplink_raw)

    # Regex to remove large spacing
    global switch_uplink
    switch_uplink = re.sub('<?\s{20}', '', switch_uplink_rmup)


def get_mac_address(net_connect_acc_sw,local_interface):
    mac_address_table = net_connect_acc_sw.send_command('show mac address-table int ' + local_interface, use_textfsm=True)
    for entry in mac_address_table: # GRAVE POF fixare asap
        return entry['destination_address']


def get_ip_arp(net_connect_dis_sw,mac_address):
    ip_arp_table = net_connect_dis_sw.send_command('show ip arp | inc ' + mac_address, use_textfsm=True)
    for entry in ip_arp_table: # GRAVE POF fixare asap
        return entry['address']


'''
Scegliere se usare, come ho fatto, comandi da terminale nelle 2 slave functions 
o se restituire dicts e poi fare ricerche algoritmiche
'''
def get_AP_info(net_connect_acc_sw,net_connect_dis_sw,switch):                     
    cdp_neighbors = net_connect_acc_sw.send_command('show cdp neighbors', use_textfsm=True)

    ap_df = pd.DataFrame(columns=('Switch','AP Name','Interface','MAC','IP'))
    ap_count = 0

    for ap in cdp_neighbors:
        if ap['platform'] == 'C9120AXI-': # GRAVE POF research better solution
            ap_name = ap['neighbor']
            ap_local_interface = ap['local_interface']
            ap_mac_address = get_mac_address(net_connect_acc_sw , ap_local_interface)
            ap_ip_address = get_ip_arp(net_connect_dis_sw , ap_mac_address)

            ap_df.loc[ap_count] = [switch,ap_name,ap_local_interface,format_mac(ap_mac_address),ap_ip_address]
            ap_count += 1
    
    return ap_df


def format_mac(mac: str) -> str:
    mac = re.sub('[.:-]', '', mac).lower()  # remove delimiters and convert to lower case
    mac = ''.join(mac.split())  # remove whitespaces
    assert len(mac) == 12  # length should be now exactly 12 (ex. 008041aefd7e)
    assert mac.isalnum()  # should only contain letters and numbers
    # convert mac in canonical form (ex. 00:80:41:ae:fd:7e)
    mac = ":".join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])
    return mac


def cmdline(command):
    process = Popen(
        args=command,
        stdout=PIPE,
        shell=True
    )
    return process.communicate()[0]


def get_camera_info(net_connect_general,switch):
    get_camera_raw = net_connect_general.send_command('show lldp neighbors', use_textfsm=True)

    camera_df = pd.DataFrame(columns=('Switch','Camera Name','Interface','MAC'))
    camera_count = 0

    for camera in get_camera_raw:
        if len(camera['neighbor']) == 4 and camera['neighbor'].isnumeric():
            camera_df.loc[camera_count] = [switch,camera['neighbor'],camera['local_interface'],format_mac(camera['neighbor_interface'])]
            camera_count += 1

    return camera_df


def get_ups_info(net_connect_dis_sw):
    get_vlan_raw = net_connect_dis_sw.send_command('show vlan brief', use_textfsm=True)
    ups_df = pd.DataFrame(columns=('Hostname','IP','MAC','VLAN'))
    ups_count = 0

    for entry in get_vlan_raw:
        if 'APC' in entry['name']:
            ups_vlan = entry['vlan_id']       # FIXME: references only the last occurrence
    
    mac_address_table = net_connect_dis_sw.send_command('show mac address-table vlan ' + ups_vlan, use_textfsm=True)  # show ip arp e salto un passaggio 
    for entry in mac_address_table:
        if 'Po' in entry['destination_port'][0]:
            mac_address = entry['destination_address']
            ip_arp = net_connect_dis_sw.send_command('show ip arp ' + mac_address, use_textfsm=True)
            if len(ip_arp) > 1:               # TODO: test for checking raw array lenght
                print("More than an IP on this MAC")
            ip_address = ip_arp[0]['address']

            byte_string = cmdline('nslookup ' + ip_address)
            string = str(byte_string,'utf-8')
            hostname = string.split(' ')[-1].rsplit('.',1)[0]

            ups_df.loc[ups_count] = [hostname,ip_address,mac_address,ups_vlan]
            ups_count += 1

    return ups_df