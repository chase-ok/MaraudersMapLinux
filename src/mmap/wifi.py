
import sys
import subprocess
import re
from functools import total_ordering

class WifiLocator(object):

    def scan(self):
        # Best strengths to worst
        return sorted(self._do_scan(), reverse=True)

    def _do_scan(self):
        # Should return a list of WifiCell s
        raise NotImplemented()

def make_locator():
    if sys.platform.startswith('linux'):
        return LinuxWifiLocator()
    else:
        return WifiLocator()

class WifiError(Exception): pass
class UnableToScanError(WifiError): pass

@total_ordering
class WifiCell(object):

    def __init__(self, address, strength, essid=None):
        self.address = address
        self.strength = strength
        self.essid = essid

    @property
    def map_strength(self):
        return self.strength + 100

    @property
    def binding_pair(self):
        return "nearest[{0}]".format(self.address), str(self.map_strength)

    def __repr__(self):
        return "WifiCell({0}, {1}, {2})"\
               .format(self.address, self.strength, self.essid)

    def __str__(self):
        return "Wifi Cell: Address={0}, Strength={1} dBm ESSID={2}"\
                .format(self.address, self.strength,
                        self.essid if self.essid else "<UNKNOWN>")

    def __lt__(self, other):
        return self.strength < other.strength

    def __eq__(self, other):
        return self.strength == other.strength


class BadScanFile(UnableToScanError):

    def __init__(self, reason, line_num=None):
        self.reason = reason
        self.line_num = line_num

class LinuxWifiLocator(WifiLocator):

    def __init__(self, interface='wlan0', use_sudo=True):
        self.interface = interface
        self.use_sudo = use_sudo
        self._parser = _IWListParser()

    def _do_scan(self):
        raw_scan = self._get_raw_scan()
        return self._parser.parse(raw_scan)

    def _get_raw_scan(self):
        command = ['iwlist', self.interface, 'scan']
        if self.use_sudo:
            command.insert(0, 'sudo')

        try:
            return subprocess.check_output(command,
                                           stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print e
            raise UnableToScanError()

class _IWListParser(object):

    def parse(self, raw_scan):
        self.lines = raw_scan.splitlines()
        self.line_num = 0

        self.skip_to_cells()
        cells = []
        while self.has_next() and self.line:
            cells.append(self.parse_cell())
        return cells


    def skip_to_cells(self):
        while not self.line.startswith('Cell'):
            self.next()

    address = 'Address', re.compile(r"Address: ([0-9A-Z:]*)")
    strength = 'Signal level', re.compile(r"Signal level=(\-?[0-9]+)")
    essid = 'ESSID', re.compile(r'ESSID:"([^"]+)"')

    def parse_cell(self):
        address = self.extract(self.address)
        while not self.line.startswith('Quality'): self.next()

        strength = self.extract(self.strength)
        while not self.line.startswith('ESSID'): self.next()
        try:
            strength = int(strength)
        except ValueError:
            raise BadScanFile('Invalid signal strength: {0}.'.format(strength),
                              self.line_num)

        essid = self.extract(self.essid)

        # Skip the rest
        while self.line and not self.line.startswith('Cell'): self.next()

        return WifiCell(address, strength, essid)

    def extract(self, section):
        name, compiled_re = section
        match = compiled_re.search(self.line)
        if match:
            return match.group(1)
        else:
            raise BadScanFile('Missing {0} section'.format(name), 
                              self.line_num)


    def next(self):
        if not self.has_next():
            raise UnableToScanError('Unexpected end of file')
        self.line_num += 1

    def has_next(self):
        return self.line_num < len(self.lines)

    @property
    def line(self):
        return self.lines[self.line_num].strip()





