# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/LICENSE

from glob import glob
from os.path import basename, join, splitext

from pylint.testutils.constants import SYS_VERS_STR


def _get_tests_info(input_dir, msg_dir, prefix, suffix):
    """get python input examples and output messages

    We use following conventions for input files and messages:
    for different inputs:
        test for python  >= x.y    ->  input   =  <name>_pyxy.py
        test for python  <  x.y    ->  input   =  <name>_py_xy.py
    for one input and different messages:
        message for python >=  x.y ->  message =  <name>_pyxy.txt
        lower versions             ->  message with highest num
    """
    result = []
    for fname in glob(join(input_dir, prefix + "*" + suffix)):
        infile = basename(fname)
        fbase = splitext(infile)[0]
        # filter input files :
        pyrestr = fbase.rsplit("_py", 1)[-1]  # like _26 or 26
        if pyrestr.isdigit():  # '24', '25'...
            if SYS_VERS_STR < pyrestr:
                continue
        if pyrestr.startswith("_") and pyrestr[1:].isdigit():
            # skip test for higher python versions
            if SYS_VERS_STR >= pyrestr[1:]:
                continue
        messages = glob(join(msg_dir, fbase + "*.txt"))
        # the last one will be without ext, i.e. for all or upper versions:
        if messages:
            for outfile in sorted(messages, reverse=True):
                py_rest = outfile.rsplit("_py", 1)[-1][:-4]
                if py_rest.isdigit() and SYS_VERS_STR >= py_rest:
                    break
        else:
            # This will provide an error message indicating the missing filename.
            outfile = join(msg_dir, fbase + ".txt")
        result.append((infile, outfile))
    return result
