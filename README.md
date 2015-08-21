# Running SocialVPN on the Controller Framework

### Usage Instructions (For Ubuntu)

#### Download and configure

* Download and extract SocialVPN
```
wget -O controller-framework-svpn_beta-v0.2.tar.gz https://goo.gl/CwBJe0
tar xvzf controller-framework-svpn_beta-v0.2.tar.gz
cd controller-framework-svpn_beta-v0.2
```
* Add the xmpp_username, xmpp_password, xmpp_host parameters to the config.json file.


#### Run SocialVPN

* Run IPOP-Tincan 
```
sudo sh -c './ipop-tincan-x86_64 1> out.log 2> err.log &'
```
* Start SocialVPN controller
```
python CFx.py -c config.json &> log.txt &
```
* Check the status 
```
echo -e '\x02\x01{"m":"get_state"}' | netcat -q 1 -u 127.0.0.1 5800
```

#### Kill SocialVPN
Find out the process IDs of IPOP Tincan and IPOP Controller using the following command
```
netstat -ntulp
```
Kill the processes using
```
kill -9 <process id>
```
