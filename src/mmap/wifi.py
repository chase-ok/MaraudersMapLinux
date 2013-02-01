
import sys
import subprocess
import re

class WifiLocator(object):

    def get_strengths(self):
        raise NotImplemented()

def make_locator():
    if sys.platform.startswith('linux'):
        return LinuxWifiLocator()
    else:
        return WifiLocator()

class UnableToScanError(Exception):
    pass

class BadScanFile(UnableToScanError):

    def __init__(self, reason, line_num=None):
        self.reason = reason
        self.line_num = line_num

class LinuxWifiLocator(WifiLocator):

    def __init__(self, interface='wlan0'):
        self.interface = interface

    def get_strengths(self):
        raw_scan = self._get_raw_scan()
        cells = self._parse_cells(raw_scan)
        return []

    def _get_raw_scan(self):
        command = ['iwlist', self.interface, 'scan']
        try:
            return subprocess.check_output(command,
                                           stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise UnableToScanError()

class _IWListParser(object):

    def parse(self, raw_scan):
        self.lines = raw_scan.splitlines()
        self.line_num = 0
        print len(self.lines)

        self.skip_to_cells()
        cells = []
        while self.has_next() and self.line:
            cells.append(self.parse_cell())
        return cells


    def skip_to_cells(self):
        while not self.line.startswith('Cell'):
            print self.line
            self.next()

    address = 'Address', re.compile(r"Address: ([0-9A-Z:]*)")
    strength = 'Signal level', re.compile(r"Signal level=(\-?[0-9]+)")
    essid = 'ESSID', re.compile(r'ESSID:"([^"]+)"')

    def parse_cell(self):
        cell = {}

        cell['address'] = self.extract(self.address)
        while not self.line.startswith('Quality'): self.next()
        cell['strength'] = self.extract(self.strength)
        while not self.line.startswith('ESSID'): self.next()
        cell['essid'] = self.extract(self.essid)

        # Skip the rest
        while self.line and not self.line.startswith('Cell'): self.next()
        return cell

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





