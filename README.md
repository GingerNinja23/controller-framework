# Running GroupVPN/SocialVPN on the Controller Framework

### Usage Instructions (For Ubuntu)

#### Download

* Download and extract the controller framework
  ```
  wget -O controller-framework-beta-v0.3.tar.gz https://goo.gl/UQHfCE
  tar xvzf controller-framework-beta-v0.3.tar.gz
  cd controller-framework-beta-v0.3
  ```

* Run IPOP-Tincan 
  ```
  sudo sh -c './ipop-tincan-x86_64 1> out.log 2> err.log &'
  ```

After starting IPOP-Tincan, you can either run the GroupVPN controller or the SocialVPN controller.

#### Running GroupVPN

* Change directory to gvpn
  ```
  cd gvpn
  ```

* Change config.json according to the requirement. Add xmpp_username, xmpp_password and xmpp_host to the config file and ensure that the IP addresses are different for all the nodes.

* Start GroupVPN controller
  ```
  python CFx.py -c config.json &> log.txt &
  ```
* Check the status 

  ```
  echo -e '\x02\x01{"m":"get_state"}' | netcat -q 1 -u 127.0.0.1 5800
  ```

#### Running SocialVPN

* Change directory to svpn
  ```
  cd svpn
  ```

* Change config.json according to the requirement. Add xmpp_username, xmpp_password and xmpp_host to the config file.

* Start SocialVPN controller
  ```
  python CFx.py -c config.json &> log.txt &
  ```
  
* Check the status 
  ```
  echo -e '\x02\x01{"m":"get_state"}' | netcat -q 1 -u 127.0.0.1 5800
  ```

#### Killing the Controller
Find out the process IDs of IPOP Tincan and IPOP Controller using the following command
  ```
  netstat -ntulp
  ```
Kill the processes using
  ```
  kill -9 <process id>
  ```
