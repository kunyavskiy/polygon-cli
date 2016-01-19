# polygon-cli
Command-line tool for polygon

##Requirments

* Python 3 (tested on 3.4)
* requests lib
* prettytable lib
* colorama lib
* diff3 avalible in path

## Supported features

* Downloadings solutions and resources from polygon.
* Uploading them back to polygon.
* Automatic merging with conflicts.
 
## Installation 

1. Install Python3 and setuputils module (for example, it goes with pip3)
2. Checkout repo using `git clone https://github.com/kunyavskiy/polygon-cli.git`
3. Run `python3 setup.py install`
  * On Linux, it will put executable polygon-cli in /usr/local/bin
  * On Windows, it will put execuable polygon-cli in Scripts directory of your Python3 installtion. It should be added to path variable for more simple usage
4. Even if it doesn't run, install the dependencies manually as below,
  * `pip3 install requests` 
  * `pip3 install colorama` 
  * `pip3 install prettytable` 


