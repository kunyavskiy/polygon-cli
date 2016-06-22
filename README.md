# polygon-cli
Command-line tool for [polygon](https://polygon.codeforces.com/)

##Requirments

* Python 3 (tested on 3.4)
* requests lib
* prettytable lib
* colorama lib
* diff3 avalible in path

## Supported features

* Download files and solutions from polygon.
* Uploading them back to polygon.
* Automatic merging with conflicts.
 
## Installation 

1. Install Python3 and setuputils module (for example, it goes with pip3)
2. Checkout repo using `git clone https://github.com/kunyavskiy/polygon-cli.git`
3. Edit config.py file. Add api\_key and api\_secret to it. If you want, you can also add
   login and password. Then it will be not asked, it not-api requests needed. 
   You should change:
   ```Python
   login = None
   password = None
   api_key = None
   api_secret = None
   ```
   to something like
   ```Python
   login = 'pkunyavskiy'
   password = None
   api_key = 'xxxxxxxxxxxxxxxxx'
   api_secret = 'xxxxxxxxxxxxxxx'
   ```

   WARNING: password and api\_key/api\_secret are stored in plain text in your Python Scripts directory.

4. Run `python3 setup.py install`
  * On Linux, it will put executable polygon-cli in /usr/local/bin
  * On Windows, it will put execuable polygon-cli in Scripts directory of your Python3 installtion. It should be added to path variable for more simple usage
5. Even if it doesn't run, install the dependencies manually as below,
  * `pip3 install requests` 
  * `pip3 install colorama` 
  * `pip3 install prettytable` 
