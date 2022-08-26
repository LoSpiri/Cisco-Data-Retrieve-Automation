from docx import Document
from docx.shared import Pt
from cisco import *
from bookwriting import *
import pandas as pd
import getpass

def run():
    # could return tuple
    # username
    username = input('Username: ')
    # password  
    password = getpass.getpass("Password: ")
    # idf_number
    distribution_hostname = input('Distribution switch hostname, with XXX replacing the idf number: ').strip()
    prev, next = distribution_hostname.split('XXX')
    if next[-11:] != '.amazon.com':
        next = next + '.amazon.com'

    number = 0
    errors = 0

    while errors<3:
        number += 1
        idf_number = str(number)

        dis_name = prev + idf_number + next
        
        # book_filename  
        # book_filename = input('Book filename (without .docx): ')
        book_filename = 'Blueprint'
        document = Document(book_filename + '.docx')

        replace_text(get_paragraph(document.paragraphs,'FC IT IDF 1 BOOK'),'IDF 1','IDF ' + idf_number)

        net_connect_dis_sw = connect_to_cisco(username,password,dis_name)
        if net_connect_dis_sw == 1:
            errors += 1
            continue
        print("Proceeding to write IDF book for: " + dis_name)

        # Retrieving switch set
        switch_set = get_neighbors_set(net_connect_dis_sw,'acc')

        # CREATE DFs
        # Aggregators df
        agg_df = get_aggregator_info(idf_number,username,password,net_connect_dis_sw)

        # UPS df
        ups_df = get_ups_info(net_connect_dis_sw)

        # Switchs df
        switch_count = 0
        switch_df = pd.DataFrame(columns=('Switch Name','IP'))
        switch_df.loc[switch_count] = [dis_name,get_switch_IP(net_connect_dis_sw)]
        switch_count += 1

        # Cameras df
        camera_df = pd.DataFrame(columns=('Switch','Camera Name','Interface','MAC'))

        # Access points df
        ap_df = pd.DataFrame(columns=('Switch','AP Name','Interface','MAC','IP'))

        # itero gli switch e concat
        for switch in sorted(switch_set): 
            print("Retrieving data from: " + switch)
            net_connect_acc_sw = connect_to_cisco(username,password,switch)
            # switch df loc
            acc_sw_IP = get_switch_IP(net_connect_acc_sw)
            switch_df.loc[switch_count] = [switch,acc_sw_IP]
            switch_count += 1
            # camera df vertical concat
            camera_df = pd.concat([camera_df,get_camera_info(net_connect_acc_sw,switch)], axis = 0)
            # AP df loc
            ap_df = pd.concat([ap_df,get_AP_info(net_connect_acc_sw,net_connect_dis_sw,switch)], axis = 0)

        style = document.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)

        df_to_table_at_position(document,switch_df,'Switch')
        df_to_table_at_position(document,camera_df,'Cameras')
        df_to_table_at_position(document,ap_df,'Access Points')
        df_to_table_at_position(document,agg_df,'Aggregators')
        df_to_table_at_position(document,ups_df,'UPS')

        document.save('IDF' + idf_number + ' Book.docx')

    print('Dovrei aver finito!')

run() 