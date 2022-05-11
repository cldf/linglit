import sys
import contextlib

from clldutils.clilib import register_subcommands, get_parser_and_subparsers, ParserError
from clldutils.loglib import Logging

import linglit.commands


def main(args=None, catch_all=False, parsed_args=None, log=None):
    parser, subparsers = get_parser_and_subparsers('linglit')
    register_subcommands(subparsers, linglit.commands)

    args = parsed_args or parser.parse_args(args=args)

    if not hasattr(args, "main"):  # pragma: no cover
        parser.print_help()
        return 1

    with contextlib.ExitStack() as stack:
        if not log:  # pragma: no cover
            stack.enter_context(Logging(args.log, level=args.log_level))
        else:
            args.log = log
        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except ParserError as e:  # pragma: no cover
            print(e)
            return main([args._command, '-h'])
        except Exception as e:  # pragma: no cover
            if catch_all:
                print(e)
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
