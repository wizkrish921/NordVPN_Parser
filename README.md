# NordVPN_Parser
Python parser for NordVPN server configs (udp and tcp settings). This script automates download of and formatting of the OpenVPN udp/tcp config scripts provided by NordVPN for dd-wrt routers from a easy to use python commadline and loads it to your DD-WRT routers in a single step.  

Use this together with DD-WRT NordVPN scripts provided by https://tobsetobse.github.io/DD-WRT_NordVPN/


Python ver 3.7.2

Usage :
       nordvpn_parser.py [-h] --base_dir BASE_DIR
                         [--config_numbers CONFIG_NUMBERS]
                         [--recommended RECOMMENDED] 
                         [--country COUNTRY]
                         [--load LOAD] 
                         [--server_name SERVER_NAME]
                         [--protocol PROTOCOL] 
                         [--router_ip ROUTER_IP]
                         [--router_user ROUTER_USER]
                         [--router_password ROUTER_PASSWORD]
                         [--router_dir ROUTER_DIR]
                         [--delete_prev_router_config DELETE_PREV_ROUTER_CONFIG]
                         [--debug DEBUG]

Arguments NordVPN server parser eg: py nvpn_parser.py --server_name us4067
--protocol udp --dir <storage dir>

optional arguments:
  -h, --help            show this help message and exit
  --base_dir BASE_DIR   Starting directory to store the server config files on your machine
  --config_numbers CONFIG_NUMBERS
                        Number of server configs to download Eg. 5
  --recommended RECOMMENDED
                        Use servers recommended by NordVPN [Y]? 
  --country COUNTRY     Country NordVPN Server is located in. Eg: "Canada" 
  --load LOAD           Server load within this range. Eg. Load = 10 will filter servers with load between 5 and 10...
  --server_name SERVER_NAME
                        NordVPN Server name, if you want to download a specific server config from NordVPN website eg us4000
  --protocol PROTOCOL   protocol udp or tcp. default is udp
  --router_ip ROUTER_IP
                        Router IP address. If provided, will move the file to the router
  --router_user ROUTER_USER
                        Router login user. If provided, will move the file to router
  --router_password ROUTER_PASSWORD
                        Router login password. If provided, will move the file to router
  --router_dir ROUTER_DIR
                        Location of router directory where these files will be pushed
  --delete_prev_router_config DELETE_PREV_ROUTER_CONFIG
                        Previous server configs on the router to be deleted. Provide config names like us4500udp or us4* etc.
                        (wildcard is supported)
  --debug DEBUG         Debug Y/N? Helps in debugging by printing additional info along the way

