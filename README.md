# polygon-cli
Command-line tool for polygon

##Requirments

* Python 3 (tested on 3.4)
* requests lib
* prettytable lib
* colorama lib
* diff3 avalible in path

## Suppoted fetures

* Downloadings solutions and resources from polygon
* Uploading them to polygon back
* Automatic merging with conflicts
 
## Installation 

1. Install Python3 and setuputils module (for example, it goes with pip3)
2. Checkout repo using `git clone https://github.com/kunyavskiy/polygon-cli.git`
3. Run `python3 setup.py install`
  * On Linux, it will put executable polygon-cli in /usr/local/bin
  * On Windows, it will put execuable polygon-cli in Scripts directory of your Python3 installtion. It should be added to path variable for more simple usage
4. If somehow it can't be run because of some modules not installed, run
  * `pip3 install requests` 
  * `pip3 install colorama` 
  * `pip3 install prettytable` 


