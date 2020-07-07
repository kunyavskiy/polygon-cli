# polygon-cli
Command-line tool for [polygon](https://polygon.codeforces.com/)

## Requirments

* Python 3 (tested on 3.4)
* requests lib
* prettytable lib
* colorama lib
* pyyaml lib
* diff and diff3 avalible in path

## Supported features

* Download files and solutions from polygon.
* Uploading them back to polygon.
* Automatic merging with conflicts.

## Installation

1. Install Python3 and setuputils module (for example, it goes with pip3)
2. Checkout repo using `git clone https://github.com/kunyavskiy/polygon-cli.git`
3. On first usage login/password/api\_key/api\_secret will be asked.
   They will be stored locally in plain text.
   You may not enter password. If you do that, some features based on html parsion, becuase of lack of api
   will not work than.

4. Run `python3 setup.py install [--user]`
  * On Linux, it will put the executable polygon-cli in /usr/local/bin
  * On Windows, it will put the executable polygon-cli in Scripts directory of your Python3 installtion. It should be added to the path variable for easier usage.

   Add the option `--user` to install as local user without root/administrator privileges.

5. Even if it doesn't run, install the dependencies manually as below,
  * `pip3 install requests`
  * `pip3 install colorama`
  * `pip3 install prettytable`
  * `pip3 install pyyaml`
