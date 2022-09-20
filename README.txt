In order to run the script, is required to first install python, alongside some packages. Follow the steps below:
-   Install python via official website
-   pip install netmiko
-   pip install pandas
-   pip install textfsm

In the provided folder you will find a file "Blueprint IDF Book", customize it to taste.

The script also requires some inputs at runtime:
-username
-password
-whid
-Your FC's AP models
	- Retrievable doing: "ssh bgy1-fc-wlc-a-1" and then: "show ap sum"

FAQ:
-   AttributeError: 'int' object has no attribute 'send_command':
    Rerun the script, possibly reducing the heavy processes in use

-   PermissionError: [Errno 13] Permission denied: 'IDF1 Book.docx':
    CLose thr referenced file, the script can't access it otherwise
 

