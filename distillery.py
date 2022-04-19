import numpy as np
import json
import scipy.interpolate as intp
from scipy import integrate
import scipy.fftpack as ft

#To do list:
# Support plotting
# Support Flask + Plotly for dynamic website
# Implement sanity checks on files (both info and lnk present in directory)
# Implement sanity checks on database (is a species with same name already in there)
# Implement calculation of optical constants/Qabs/dielectric functions from given values

def ReadData(species=None):
#function to read in a formatted text file for a single species
    
    # lnk file has 3 columns, space delimited
    # wavelength (um), n, k
    with open('./data/'+species+'.lnk', 'r') as f:
        lnk_table = f.readlines()

    l = []
    n = []
    k = []
    for line in lnk_table:
        line.strip()
        line_split = line.split()

        l.append(float(line_split[0]))
        n.append(float(line_split[1]))
        k.append(float(line_split[2]))

    # info file has 7 lines, citations are ';' delimited
    # species
    # formula
    # density (in gcm^-3)
    # temperature (in K)
    # type (PYROXINE, SILICATE, etc.)
    # origin (one of LABORATORY, CALCULATION, or HYBRID)
    # citation(s)
    with open('./data/'+species+'.info', 'r') as f:
        info_table = f.readlines()

    mydict = {'species': info_table[0].strip(),
              'wavelength': l,
              'n': n,
              'k': k,
              'formula': info_table[1].strip(),
              'density': float(info_table[2].strip()),
              'temperature': float(info_table[3].strip()),
              'stype' : info_table[4].strip(),
              'origin' : info_table[5].strip(),
              'citation': info_table[6].strip()
              }

    return mydict

def ReadJSON(species=None):
#function to write a json file for a single species
    with open('./json/'+species+'.json', 'r') as payload:
        mydict = json.load(payload)

    return mydict

def WriteJSON(mydict):
#function to write a json file for a single species
    with open('./json/'+mydict['species']+'.json', 'w') as payload:
        json.dump(mydict, payload)

#
# Here we define the functions that manipulate the optical constants
#
def kramers_kronig(data_array):

    for i in range(0,len(data_array)):

        data = data_array[i]

        wavelength = np.asarray(data['wavelength'])
        ref_re = np.asarray(data['n'])
        ref_im = np.asarray(data['k'])

    #ref_im = np.asarray(data_array['k'])
    #ref_re = np.asarray(data_array['n'])
    #wavelength = np.asarray(data_array['wavelength'])
    
    # the wavelength might become a parameter to set as an input for the user in a later version! 

    wavelength_range = [np.min(wavelength), np.max(wavelength)]
    
    chir = ref_re ** 2 - ref_im ** 2
    chii = 2 * ref_re * ref_im
    
    min_step = np.min(np.diff(wavelength))
    nsteps = int((wavelength_range[1] - wavelength_range[0]) / min_step)
    w_grid = np.linspace(wavelength_range[0], wavelength_range[1], nsteps)
    
    interp_imag_dielectric_func2 = intp.interp1d(wavelength, chii, kind='linear', fill_value=0.,bounds_error=False, assume_sorted=True)
    chii_intp2=interp_imag_dielectric_func2(w_grid)
    
    chir_trans_grid = ft.hilbert(chii_intp2[::-1])[::-1]
    chir_zero = integrate.simpson((chii_intp2 / (1 / w_grid))[::-1], (1 / w_grid)[::-1])
    shift = chir_zero - chir_trans_grid[-1]
    chir_trans_grid += shift
    
    f = intp.interp1d(w_grid, chir_trans_grid)
    chir_trans = f(wavelength)
    
    # transforming back to n and k

    chi = chir_trans + 1.0j * chii
    kk_n = np.sqrt((np.abs(chi) + chir_trans) / 2.0)
    kk_k = np.sqrt((np.abs(chi) - chir_trans) / 2.0)
    kk_l = wavelength        

    return kk_l,kk_n, kk_k

def Bruggeman(data_array):
  print("Not yet implemented.")

  return wave,nn,kk

def MaxwellGarland(data_array):
  print("Not yet implemented.")

  return wave,nn,kk

