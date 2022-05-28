# polygon-cli
Command-line tool for [polygon](https://polygon.codeforces.com/)

## Requirements

* Python 3 (tested on 3.4)
* requests lib
* prettytable lib
* colorama lib
* pyyaml lib
* diff and diff3 available in path

## Supported features

* Download files and solutions from polygon.
* Uploading them back to polygon.
* Automatic merging with conflicts.

## Installation

### Using pip3

Run `pip3 install polygon-cli`

### Using the source code

1. Install Python3 and setuputils module (for example, it goes with pip3)
2. Checkout repo using `git clone https://github.com/kunyavskiy/polygon-cli.git`

3. Run `python3 setup.py install [--user]`

      * On Linux, it will put the executable polygon-cli in /usr/local/bin
      * On Windows, it will put the executable polygon-cli in Scripts directory of your Python3 installation. It should be added to the path variable for easier usage.

   Add the option `--user` to install as local user without root/administrator privileges.

4. Even if it doesn't run, install the dependencies manually as below,
  * `pip3 install requests`
  * `pip3 install colorama`
  * `pip3 install prettytable`
  * `pip3 install pyyaml`

## Running and authentication

Run using `polygon-cli` command.

Usually the usage starts with (use problem short name or problem id instead of `aplusb`):
   * `polygon-cli init aplusb`
   * `polygon-cli update`

The commands above create a working copy in the current folder. Use `polygon-cli -h` to see other commands of the client.

On the first usage login, password, api_key and api_secret will be asked.

They will be stored locally in plain text.

You may leave password field empty. If you do that, some features based on html parsing, because of lack of api will not work then.
