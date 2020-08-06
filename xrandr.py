from re import compile
from shutil import which
from subprocess import run, PIPE
from collections import OrderedDict


# Thank you https://regex101.com/r/WcDhxd/1
XRANDR_REGEX = compile(
    r'^(?P<name>[a-zA-Z0-9_-]+) connected (?P<primary>primary)? ?'
    r'(?P<width>[0-9]+)x(?P<height>[0-9]+)\+'
    r'(?P<x_offset>[0-9]+)\+(?P<y_offset>[0-9]+).*$'
)


def parse_xrandr():
    xrandr = which('xrandr')
    if not xrandr:
        raise RuntimeError('The xrandr executable is missing')

    result = run(
        [xrandr],
        check=True,
        stdout=PIPE,
        # This actually means open in text mode with system encoding, yeah
        universal_newlines=True,
    )

    output = OrderedDict()

    for line in result.stdout.strip().splitlines():
        match = XRANDR_REGEX.match(line)
        if not match:
            continue

        groups = match.groupdict()
        output[groups['name']] = {
            'width': int(groups['width']),
            'height': int(groups['height']),
            'x_offset': int(groups['x_offset']),
            'y_offset': int(groups['y_offset']),
            'primary': bool(groups['primary']),
        }

    return output


def calculate_virtual_space(displays):
    farthest_x, farthest_y = tuple(
        max(
            displays.values(),
            key=lambda e: e[axis]
        )
        for axis in ('x_offset', 'y_offset')
    )

    vspace_w, vspace_h = (
        farthest_x['x_offset'] + farthest_x['width'],
        farthest_y['y_offset'] + farthest_y['height'],
    )

    return (vspace_w, vspace_h)


__all__ = [
    'parse_xrandr',
    'calculate_virtual_space',
]
