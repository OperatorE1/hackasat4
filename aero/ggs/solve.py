from numpy import radians
from scipy.constants import kilo

from orbital import earth, KeplerianElements, plot


a = KeplerianElements(a=63780000.0, e=0.3, i=1.0995574287564276, raan=0.4363323129985824, arg_pe=1.361356816555577, M0=0.17453292519943295, body='earth', ref_epoch='2022-01-01T00:00:00.000')


