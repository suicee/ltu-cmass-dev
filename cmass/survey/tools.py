"""
Functions for implementing BOSS-cmass forward models.
Many functions are from or inspired by: https://github.com/changhoonhahn/simbig/blob/main/src/simbig/forwardmodel.py
"""
# imports
import os
from os.path import join as pjoin
import numpy as np
import pymangle
from astropy.io import fits
import pandas as pd

from ..utils import timing_decorator

# mask functions


def BOSS_angular(ra, dec):
    ''' Given RA and Dec, check whether the galaxies are within the angular
    mask of BOSS
    '''
    f_poly = os.path.join('data', 'obs', 'mask_DR12v5_CMASS_North.ply')
    mask = pymangle.Mangle(f_poly)

    w = mask.weight(ra, dec)
    inpoly = (w > 0.)
    return inpoly


def BOSS_veto(ra, dec, verbose=False):
    ''' given RA and Dec, find the objects that fall within one of the veto 
    masks of BOSS. At the moment it checks through the veto masks one by one.  
    '''
    in_veto = np.zeros(len(ra)).astype(bool)
    fvetos = [
        'badfield_mask_postprocess_pixs8.ply',
        'badfield_mask_unphot_seeing_extinction_pixs8_dr12.ply',
        'allsky_bright_star_mask_pix.ply',
        'bright_object_mask_rykoff_pix.ply',
        'centerpost_mask_dr12.ply',
        'collision_priority_mask_dr12.ply']

    veto_dir = 'data'
    for fveto in fvetos:
        if verbose:
            print(fveto)
        veto = pymangle.Mangle(os.path.join(veto_dir, 'obs', fveto))
        w_veto = veto.weight(ra, dec)
        in_veto = in_veto | (w_veto > 0.)
    return in_veto


def BOSS_redshift(z):
    zmin, zmax = 0.4, 0.7
    mask = (zmin < z) & (z < zmax)
    return np.array(mask)


def BOSS_area():
    f_poly = os.path.join('data', 'obs/mask_DR12v5_CMASSLOWZ_North.ply')
    boss_poly = pymangle.Mangle(f_poly)
    area = np.sum(boss_poly.areas * boss_poly.weights)  # deg^2
    return area


@timing_decorator
def gen_randoms():
    fname = 'data/obs/random0_DR12v5_CMASS_North.fits'
    fields = ['RA', 'DEC', 'Z']
    with fits.open(fname) as hdul:
        randoms = np.array([hdul[1].data[x] for x in fields]).T
        randoms = pd.DataFrame(randoms, columns=fields)

    n_z = np.load(pjoin('data', 'obs', 'n-z_DR12v5_CMASS_North.npy'),
                  allow_pickle=True).item()
    be, hobs = n_z['be'], n_z['h']
    cutoffs = np.cumsum(hobs) / np.sum(hobs)
    w = np.diff(be[:2])[0]

    prng = np.random.uniform(size=len(randoms))
    randoms['Z'] = be[:-1][cutoffs.searchsorted(prng)]
    randoms['Z'] += w * np.random.uniform(size=len(randoms))

    # further selection functions
    mask = BOSS_angular(randoms['RA'], randoms['DEC'])
    randoms = randoms[mask]
    mask = BOSS_redshift(randoms['Z'])
    randoms = randoms[mask]
    mask = (~BOSS_veto(randoms['RA'], randoms['DEC'], verbose=True))
    randoms = randoms[mask]

    return randoms.values
