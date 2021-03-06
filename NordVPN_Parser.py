#*--------------------------------------------------------------------*
# NordVPN Parser --
#  - parse VPN server config files (ovpn) and download to a dd-wrt router
# 
# wizkrish921
#*--------------------------------------------------------------------*
import datetime
import sys
import urllib.request
import argparse
import os
import re
import pysftp
import json
import requests
from pathlib import Path
import posixpath
import pandas as pd
from pandas.io.json import json_normalize
from flatten_json import flatten
import pprint
from geopy.geocoders import Nominatim
from math import cos, sqrt

#*--------------------------------------------------------------------*

def parse_command_line_args():
	"""Parse command line arguments."""

	parser = argparse.ArgumentParser(description='Arguments NordVPN server parser eg: \n py nvpn_parser.py --server_name us4067 --protocol udp --dir <storage dir>')
	parser.add_argument(
	'--base_dir', required=False, default = 'serverconfigs', help='Starting directory to store the server config files')
	parser.add_argument(
	'--config_limit', required=False, default=1, help='Number of configs to download')
	parser.add_argument(
	'--recommended', required=False, default= 'N', help='Use servers recommended by NordVPN [Y]?')
	parser.add_argument(
	'--country', required=False, help='Country NordVPN Server is located in. use comma for multiple countries. Eg. us,uk,de etc. ')
	parser.add_argument(
	'--city', required=False, help='City name for nearest server...')
	parser.add_argument(
	'--load', required=False, default=10, help='Server load within this range. Eg. Load = 10 will filter servers with load between 5 and 10...')
	parser.add_argument(
	'--server_name', required=False, help='NordVPN Server name eg us4000')
	parser.add_argument(
	'--protocol', required=False, default='udp', help='protocol udp or tcp. default is udp ')
	parser.add_argument(
	'--router_ip', required=False, help='Router IP address. If provided, will move the file to router')
	parser.add_argument(
	'--router_user', required=False, help='Router login user. If provided, will move the file to router')
	parser.add_argument(
	'--router_password', required=False, help='Router login password. If provided, will move the file to router')
	parser.add_argument(
	'--router_dir', required=False, default='/jffs/serverconfigs', help='Location of router directory where these files will be pushed')
	parser.add_argument(
	'--delete_prev_router_config', required=False, help='Previous server configs on the router to be deleted. Provide config names like us4500udp or us4* etc. (wildcard supported)')
	parser.add_argument(
	'--debug', required=False, default=0, help= 'Debug level 0,1,2,3? Helps in debugging by printing additional info along the way' )

	return parser.parse_args()


#--------------------------------------------------------------#	
def whoami(): 
	
	x_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	return f'\n{x_time} : function : {sys._getframe(1).f_code.co_name}'


#--------------------------------------------------------------#	
def distance(lon1, lat1, lon2, lat2) :

	#if args.debug >=1 : print(whoami())
	
	## If city arg not passed or not found, lat2, lon2 are -999, -999, return distance =0
	if lat2 == -9999 and lon2 == -9999 : return 0
	
	R = 6371000 #radius of the Earth in m 
	x = (lon2-lon1) * cos(0.5*(lat2+lat1))
	y = (lat2-lat1)
	
	return R * sqrt(x*x + y*y)
	
#--------------------------------------------------------------#	

def get_geo_location(city_name) :
	
	if args.debug >=1 : print(whoami())

	
	geolocator = Nominatim(user_agent='myapplication')
	location = geolocator.geocode(city_name)
	city = location.raw
	
	if args.debug >=2 : pprint.pprint(city)
	
	return (city)

#--------------------------------------------------------------#
def get_server_config(url, dir, server_name, protocol) :

	if args.debug >=1 : print(whoami())
	if args.debug >= 1  : print(f'\nDownload NordVPN config file for : {server_name}{protocol}\n')
	
	response = urllib.request.urlopen(url)
	data = response.read()      # a `bytes` object
	contents = data.decode('utf-8') # a `str`; this step can't be used if data is binary

	vpn_conf  = contents[contents.find("client"):contents.find("<ca>")-2]
	vpn_conf = re.sub('dev tun', '', vpn_conf)
	vpn_conf = re.sub('auth-user-pass', '', vpn_conf)
	if args.debug >= 3 : print(vpn_conf)

	ca_crt = contents[contents.find("<ca>")+5:contents.find("</ca>")]
	if args.debug >= 3 : print(ca_crt)

	ta_key = contents[contents.find("<tls-auth>")+11:contents.find("</tls-auth>")]
	if args.debug >= 3 : print(ta_key)

	remote = contents[contents.find("remote")-1:contents.find("1194")+4]
	if args.debug >= 3 : print(remote)


	## Write serverconfigs to local directory...
	p = Path(dir)
	if p.exists() == False :
		os.mkdir(dir)
		
	write_dir = posixpath.join(dir, server_name+protocol)
	
	if args.debug >= 1 : print(f'Local Dir for writing configs: {write_dir}')
	p = Path(write_dir)

	if p.exists() == False :
		os.mkdir(write_dir)
	elif p.is_dir() == False :
		print(f'Error!!\n **{write_dir} ** is an existing file. \n\tDownload halted. Please check/remove this file and try again.\n')
		return -1

	## write ca_crt
	f=open(write_dir+'/ca.crt','w')
	f.write(ca_crt)
	f.close()

	## write ta.keys
	f=open(write_dir+'/ta.key','w')
	f.write(ta_key)
	f.close()

	## static text for open.conf - add these lines to the end of openvpn.conf 
	static_text = " \n\
	key-direction 1 \n\
	\n\
	ca /tmp/openvpncl/ca.crt \n\
	writepid /var/run/openvpncl.pid \n\
	auth-user-pass /tmp/openvpncl/credentials \n\
	tls-auth /tmp/openvpncl/ta.key 1 \n\
	syslog \n\
	script-security 2 \n\
	dev tun1 \n\
	"
	
	
	## write openvpncl.config
	f=open(write_dir+'/openvpn.conf','w')
	f.write(vpn_conf + static_text)
	f.close()
	
	if args.router_ip is not None :
		#sFTP configs to router...
		if args.debug >=1 :  print(f'sFTP to {args.router_ip}')
				
		# Loads .ssh/known_hosts    
		cnopts = pysftp.CnOpts()
		cnopts.hostkeys = None

		with pysftp.Connection(args.router_ip, username=args.router_user, password=args.router_password, cnopts=cnopts) as sftp:
			r_dir = posixpath.join(args.router_dir, server_name+protocol)
			#r_dir = f'{args.router_dir}/{server_name}{protocol}/'
			if args.debug >= 1 : print(f'Remote Dir:{r_dir}')
			
			if sftp.exists(args.router_dir) == False :
				print(f'Remote Directory : {args.router_dir} doesn\'t exist. Check the parameters and try again!')
				return
								
			if sftp.exists(r_dir) == False:
				print(f'Make Dir in router: {r_dir}')
				sftp.mkdir(r_dir)
				
			sftp.put(write_dir+'/ca.crt', r_dir+'/ca.crt')
			sftp.put(write_dir+'/ta.key', r_dir+'/ta.key')
			sftp.put(write_dir+'/openvpn.conf', r_dir+'/openvpn.conf')
			sftp.close()
		
			if args.debug >= 1 : print(f'Downloaded {server_name}{protocol} to {args.router_ip}') 
	

#-----------------------------------------------------------
def construct_server_url(server_name, protocol, dir) :

	if args.debug >=1 : print(whoami())
	
	url = f'https://downloads.nordcdn.com/configs/files/ovpn_{protocol}/servers/{server_name}.nordvpn.com.{protocol}.ovpn'

	if args.debug >= 3 :
		print("Server Name " + server_name)
		print("Protocol " + protocol)
		print("Directory " + dir)
		print('getting config from')
		print(url)

	## Now get the actual server config files ....uncomment to run
	get_server_config(url, dir, server_name, protocol)


#-----------------------------------------------------------
# Delete Router Config...

def delete_router_config(router_path, router_dir) :

	if args.debug >= 1 : print(whoami())
	if args.debug >= 1 :  print(f'sFTP to {args.router_ip}')
				
	# Loads .ssh/known_hosts    
	cnopts = pysftp.CnOpts()
	cnopts.hostkeys = None

	with pysftp.Connection(args.router_ip, username=args.router_user, password=args.router_password, cnopts=cnopts) as conn:
		r_dir = posixpath.join(router_path, router_dir)
		
		if args.debug >= 1 : print(f'Remote Dir:{r_dir}')

		if conn.exists(router_path) == False:
			print(f'Remote dir doesn\'t exist - {router_path}. Config files were NOT deleted.')
			return
				
		conn.execute(f'rm -r {r_dir}')
		
		if args.debug >= 1 : print(f'Current Router Configs: {conn.listdir(router_path)}')
		
		conn.close()
			
	return

#-----------------------------------------------------------
# NordVPN Recommended Servers : Load and manipulate JSON server data in dataframe to get the top server names with least loads...

def load_reco_df(data) :

	if args.debug >=1 : print(whoami())
	
	flat_data = (flatten(d) for d in data)
	
	df = pd.DataFrame(flat_data)
	df1 = df.sort_values(by=['load'], ascending=True)
	df1 = df[df['technologies_1_name'] == 'OpenVPN UDP']
	df2 = df1['hostname']
		
	server_list = df2.values.tolist()
	
	if args.debug >= 2 : 
		df3 = df1.filter(items=['load', 'hostname', 'ips_0_ip_ip', 'locations_0_country_city_name'])
		print(f'Data Frame Head(20):\n {df3.head(20)}')
		
	if args.debug >= 1 : print(f'Data Frame Rows : {len(df)}')
	if args.debug >= 3 : print(f'Server list  : {server_list}')
	
	i=0
	while i < int(args.config_limit) :
		domain_name = str(server_list[i])
		server_name= domain_name.split('.')[0]
		if args.debug >= 2 : print(f'Server #{i}  -  {server_name}')
		
		construct_server_url(server_name, args.protocol, args.base_dir)
		i += 1
		if i >= len(server_list) : 
			print(f'Exhausted available servers. Downloading only {i} server configs ') 
			break
	return
	

#-----------------------------------------------------------
# Load and manipulate JSON server data in dataframe to get the top server names with least loads...

def load_df(data) :

	if args.debug >=1 : print(whoami())
	
	flat_data = (flatten(d) for d in data)
	df = pd.DataFrame(flat_data)
	
	## Apply filters to the server list _ only udp/tcp servers, country filter...
	df1 = df[df['features_openvpn_udp'] == True]
	if args.country is not None : df1 = df1[df1['country'] == (args.country)] 
	
	## City parameter, get nearest Lat & Long...
	df1['distance'] = df1.apply(lambda row: distance(float(row['location_lat']), float(row['location_long']), float(city["lat"]), float(city["lon"]) ), axis = 1)
			
	df1 = df1[df1['load'].between(int(args.load)-5, int(args.load)+5, inclusive=True)] 
	df1 = df1.sort_values(by=['distance', 'load'], ascending=[True, True])
		
	df2 = df1['domain']
	server_list = df2.values.tolist()
	
	if args.debug >= 2 : pprint.pprint(f'Data Frame Columns:\n {list(df1.columns)}')
	if args.debug >= 2 : 
		df3 = df1.filter(items=['load', 'domain', 'ip_address', 'country', 'location_lat', 'location_long', 'distance'])
		print(f'Data Frame Head(20):\n {df3.head(20)}')
		
	if args.debug >= 1 : print(f'Data Frame Rows : {len(df)}')
	if args.debug >= 3 : print(f'Server list  : {server_list}')
			
	i=0
	while i < int(args.config_limit) :
		domain_name = str(server_list[i])
		server_name= domain_name.split('.')[0]
		if args.debug >= 2 : print(f'{i}  -  {server_name}')
		
		construct_server_url(server_name, args.protocol, args.base_dir)
		i += 1
		
		if i >= len(server_list) : 
			print(f'Exhausted available servers. Downloading only {i} server configs ') 
			break
		
	return
#-----------------------------------------------------------
# - Start Main module ------  
## Main()

## init & parse arguments/variables 
args = parse_command_line_args()
args.debug = int(args.debug)

if args.debug >=1 : print(whoami())

## if delete configs parameter is passed, get delete existing server configs from the router first
if  args.delete_prev_router_config is not None :
	if args.router_dir is not None and args.router_ip is not None and args.router_user is not None and args.router_password is not None :
		print (f'This will delete the config files in the router. Are you sure???')
		input("Press Ctrl+C to cancel!! any other key to continue...")
		delete_router_config(args.router_dir, args.delete_prev_router_config)
		
	else:
		print (f'Cannot delete config files. Missing Parameters for connecting to router. Try again')

##	IF recommended arg is passed, get recommended servers...
if args.recommended == 'Y' :
	print(f'You chose to use NordVPN recommended servers. Other parameters like Server name, Country, Load etc. will ignored.')
	## load servers from NordVPN recommendations as json obj
	response = requests.get("https://api.nordvpn.com/v1/servers/recommendations")
	reco_servers = json.loads(response.text)

	## load recommended servers into Data Frame & manipulate and iteratively calls construte_server_url...
	load_reco_df(reco_servers)
	
else :
	## if specific server name is passed, get its config first...
	if args.server_name is not None :
		construct_server_url(args.server_name, args.protocol, args.base_dir)

	##Check to see if other arguments like Server_name, Country, load etc. were passed, if not, just exit - you are done.
	city = {'display_name': '', 'lat': '-9999', 'lon': '-9999' }
	
	if args.city is not None :
		city = get_geo_location(args.city)
		if args.debug >= 1 : pprint.pprint(f'City info : {city["display_name"]} : Lat = {city["lat"]}, Long = {city["lon"]}')
		
	## load all servers from NordVPN as json obj
	response = requests.get("https://api.nordvpn.com/server")
	r_servers = json.loads(response.text)
	
	if args.debug >= 3 : pprint.pprint(r_servers)
		
	## load into Data Frame & manipulate and iteratively calls construte_server_url...
	load_df(r_servers)


#---------------------------------------------------------	
# This is the end!
print('\n\nNordVPN Parser - All done!!\n')