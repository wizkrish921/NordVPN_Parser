## # NordVPN_Parser

## Synopsis
The purpose of this project is to automate the download the OpenVPN configuration files provided by NordVPN for connecting to their VPN service and load it to a router running DD-WRT using a single command. 

Use this together with DD-WRT NordVPN scripts provided by https://tobsetobse.github.io/DD-WRT_NordVPN/

The script by Tobse has done a wonderful job of automatically connecting to a list of NordVPN servers for a secure VPN internet connection. It also monitors the speed of a connection and if the speed falls below your defined threshold, it reconnect to a different VPN server from the available list of servers loaded in your server.

The <b>NordVPN_Parser</b> fills a specific problem with the above script. The above script expects all the NordVPN server configs to be preloaded to the router to make the connection. It also requires user to either manually parse and upload new configurations to the router or a cumbersome php/website setup to parse and load these new configurations to the router. 
Over time, the router will have a lot of unused server config files that it has to iterate through to connect to a well performing VPN server (Well performing = Fast, low latency VPN connection). This slows down the ability of the router to quickly find and get the VPN connection.

Using <b>NordVPN_Parser</b>, you can remove this bottleneck. You can now quickly download only a subset of servers you are interested in connecting from over 5000+ NordVPN servers in multiple countries. You can also delete and reload new set of server configs easily so, you can change your connection pattern frequently without spending a lot of time downloading, parsing and loading to the router.

NordVN has released a recomendation option to provide you with the best servers to connect to by your current location and server load. This parser leverages that and downloads these server configs (just pass --recommended flag).

You can also use <b>NordVPN_Parser</b> independently to update your OpenVPN setting in DD-WRT by running this script to download the config files locally to your machine and pasting that information to the necessary blocks of the OpenVPN UI page.

## Pre-requists

Runs on Windows and Linux
Requires Python 3.7+ (I tested this on Python 3.7.2) with additional libraries.


## Usage :
The command line option allows for various parameters to be passed which are detailed below. The only required parameter is '--base_dir' which is your current local storage directory to download the script from NordVPN server. 

       Simple example
            py nvpn_parser.py --base_dir 'C:\Users\Joe\NordVPN'

       To download 5 Server configurations from NordVPN Recommended servers
            py nvpn_parser.py --base_dir 'C:\Users\Joe\NordVPN' --config_limit 5 --recommended Y
              

Here is the complete list of parameters available with this utility.

       nordvpn_parser.py [-h] --base_dir BASE_DIR
                         [--config_limit CONFIG_LIMIT]
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


       optional arguments:
              -h, --help            show this help message and exit
              --base_dir BASE_DIR   Directory to store the server config files on your machine
              --config_limit CONFIG_LIMIT
                                    Number of server configs to download Eg. 5 will download 5 server configs. Default is 1.
              --recommended RECOMMENDED
                                    Use servers recommended by NordVPN [Y]? 
              --country COUNTRY     Country NordVPN Server is located in. Eg: "Canada" 
              --load LOAD           Server load within this range. Eg. --load 10 will filter servers with load between 5 and 10...
              --server_name SERVER_NAME
                                    NordVPN Server name, if you want to download a specific server config from NordVPN website eg us4000
              --protocol PROTOCOL   protocol udp or tcp. default is udp
              --router_ip ROUTER_IP Router IP address. If provided, will move the file to the router
              --router_user ROUTER_USER
                                    Router login user. If provided, will move the file to router
              --router_password ROUTER_PASSWORD
                                    Router login password. If provided, will move the file to router
              --router_dir ROUTER_DIR
                                    Location of router directory where these files will be pushed
              --delete_prev_router_config DELETE_PREV_ROUTER_CONFIG
                                    Deletes previously stored server configs from the router. Provide config names like us4500udp or us4* etc. (wildcard is supported)
              --debug DEBUG         Debug Y/N? Helps in debugging by printing additional info along the way...

