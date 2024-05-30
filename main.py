import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from tgbot.cli import cli


def main():
    cli()


if __name__ == '__main__':
    main()
