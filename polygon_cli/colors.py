import colorama

colorama.init(autoreset=True)


def colored(color):
    return lambda message, *args: color + message.format(*args) + colorama.Style.RESET_ALL


error = colored(colorama.Fore.RED)
warning = colored(colorama.Fore.YELLOW)
success = colored(colorama.Fore.GREEN)
info = colored(colorama.Fore.CYAN)
