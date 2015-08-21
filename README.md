# Running GroupVPN on the Controller Framework

### Usage Instructions (For Ubuntu)

#### Download and configure

* Download and extract GroupVPN
```
wget -O controller-framework-gvpn_beta-v0.3.tar.gz https://goo.gl/UBQJPy
tar xvzf controller-framework-gvpn_beta-v0.3.tar.gz
cd controller-framework-gvpn_beta-v0.3
```
* Change config.json according to the requirement. Add xmpp_username, xmpp_password and xmpp_host to the config file. Ensure that the IP addresses are different for all the nodes.


#### Run GroupVPN

* Run IPOP-Tincan 
```
sudo sh -c './ipop-tincan-x86_64 1> out.log 2> err.log &'
```
* Start GroupVPN controller
```
python CFx.py -c config.json &> log.txt &
```
* Check the status 
```
echo -e '\x02\x01{"m":"get_state"}' | netcat -q 1 -u 127.0.0.1 5800
```

#### Kill GroupVPN
Find out the process IDs of IPOP Tincan and IPOP Controller using the following command
```
netstat -ntulp
```
Kill the processes using
```
kill -9 <process id>
```
