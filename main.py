from docx import Document
from docx.shared import Pt
from cisco import *
from bookwriting import *
import threading
import pandas as pd
import getpass


class myThread (threading.Thread):
   def __init__(self, numberlock, errorlock):
      threading.Thread.__init__(self)
      self.numberlock = numberlock
      self.errorlock = errorlock
   def run(self):
      print ("Starting IDF " + self.number)
      create_book(self.numberlock, self.errorlock)
      print ("Exiting IDF " + self.number)



def create_book(numberlock, errorlock):
    while(error < 3):
        numberlock.acquire()
        number += 1
        numberlock.release()
        idf_number = str(number)

        dis_name = prev + idf_number + next
        
        # book_filename  
        # book_filename = input('Book filename (without .docx): ')
        book_filename = 'Blueprint'
        document = Document(book_filename + '.docx')

        replace_text(get_paragraph(document.paragraphs,'FC IT IDF 1 BOOK'),'IDF 1','IDF ' + idf_number)

        net_connect_dis_sw = connect_to_cisco(username,password,dis_name)
        if net_connect_dis_sw == 1:
            errorlock.acquire()
            error += 1
            errorlock.release()
        print("Proceeding to write IDF book for: " + dis_name)

        # Retrieving switch set
        switch_set = get_neighbors_set(net_connect_dis_sw,'acc')

        # CREATE DFs
        # Aggregators df
        agg_df = get_aggregator_info(idf_number,username,password,net_connect_dis_sw)

        # UPS df
        ups_df = get_ups_info(net_connect_dis_sw, ups_vlan)

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
        #   Retrieving data from: bgy1-fc-acc-sw-2-1.amazon.com
        #   Retrieving data from: bgy1-fc-acc-sw-2-10.amazon.com
            print("Retrieving data from: " + switch)
            net_connect_acc_sw = connect_to_cisco(username,password,switch)
            # switch df loc
            acc_sw_IP = get_switch_IP(net_connect_acc_sw)
            switch_df.loc[switch_count] = [switch,acc_sw_IP]
            switch_count += 1
            # camera df vertical concat
            camera_df = pd.concat([camera_df,get_camera_info(net_connect_acc_sw,switch)], axis = 0)
            # AP df loc
            ap_df = pd.concat([ap_df,get_AP_info(net_connect_acc_sw,net_connect_dis_sw,switch, device_models)], axis = 0)
            net_connect_acc_sw.disconnect()
        
        net_connect_dis_sw.disconnect()

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
    
    return 0




def run():
    # could return tuple
    # username
    global username, password, prev, next, device_models, ups_vlan, number, error
    numberlock = threading.Lock()
    errorlock = threading.Lock()
    username = input('Username: ')
    # password  
    password = getpass.getpass("Password: ")
    # idf_number
    distribution_hostname = input('Distribution switch hostname, with XXX replacing the idf number: ').strip()
    prev, next = distribution_hostname.split('XXX')
    if next[-11:] != '.amazon.com':
        next = next + '.amazon.com'

    ups_vlan = input("Enter UPS vlan (Retrievable running 'sh vlan brief' in any device) :")

    device_models = []
    while(True):
        full_model = input("Insert all access points models, when finished input 'end' (Retrievable running 'sh cdp ne' in an acc-sw): ")
        model = full_model.split('-')[0]
        if model == 'end': break
        device_models.append(model)

    number = 0
    error = 0

    for i in range(4):
        thread = myThread(numberlock, errorlock)
        thread.start()

    print('Dovrei aver finito!')

run() 