#!/usr/bin/env python
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# PYTHON_ARGCOMPLETE_OK - enables optional bash tab completion

import compatibility_check  # noqa: F401
from btcrecover import btcrpass
import sys
import multiprocessing


def _print_start_banner():
    print()
    print(
        "Starting",
        btcrpass.full_version(),
        file=sys.stderr
        if any(a.startswith("--listp") for a in sys.argv[1:])
        else sys.stdout,
    )


def main():
    _print_start_banner()

    # Use existing btcrpass argument parsing and core logic
    btcrpass.parse_arguments(sys.argv[1:])
    (password_found, not_found_msg) = btcrpass.main()

    # Your triggerable event hook:
    # when a password/key is found, call out to your own logic.
    if isinstance(password_found, str):
        try:
            from orchestrator import handle_recovered  # your module, later
            handle_recovered(password_found)
        except ImportError:
            # orchestrator not present yet; do nothing extra
            pass

    # Preserve original exit behavior
    if isinstance(password_found, str):
        btcrpass.safe_print("Password found: '" + password_found + "'")
        if any(ord(c) < 32 or ord(c) > 126 for c in password_found):
            print(
                "HTML Encoded Password: '"
                + password_found.encode("ascii", "xmlcharrefreplace").decode()
                + "'"
            )
        retval = 0
    elif not_found_msg:
        print(
            not_found_msg,
            file=sys.stderr if btcrpass.args.listpass else sys.stdout,
        )
        retval = 0
    else:
        retval = 1

    for process in multiprocessing.active_children():
        process.join(1.0)

    return retval


if __name__ == "__main__":
    sys.exit(main())

