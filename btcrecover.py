#!/usr/bin/env python
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/
#
# PYTHON_ARGCOMPLETE_OK - enables optional bash tab completion

import compatibility_check  # noqa: F401  (import triggers checks)
from btcrecover import btcrpass
import sys
import multiprocessing

from orchestrator import run_recovery_pipeline


def _print_start_banner():
    print()
    print(
        "Starting",
        btcrpass.full_version(),
        file=sys.stderr
        if any(a.startswith("--listp") for a in sys.argv[1:])
        else sys.stdout,
    )


if __name__ == "__main__":
    _print_start_banner()

    # Let btcrpass own CLI parsing as before
    btcrpass.parse_arguments(sys.argv[1:])

    # Hand off to the higher‑level pipeline
    retval = run_recovery_pipeline(sys.argv[1:])

    # Wait for any remaining child processes to exit cleanly
    for process in multiprocessing.active_children():
        process.join(1.0)

    sys.exit(retval)
