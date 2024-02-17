import numpy as np
import json
import io
import scipy.interpolate as intp
from scipy import integrate
import copy
from scipy.optimize import fsolve
import scipy.fftpack as ft
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import uuid
import subprocess
from astropy.io import ascii

#To do list:
# Support plotting
# Support Flask + Plotly for dynamic website
# Implement sanity checks on files (both info and lnk present in directory)
# Implement sanity checks on database (is a species with same name already in there)
# Implement calculation of optical constants/Qabs/dielectric functions from given values

def ReadData(species=None):
#function to read in a formatted text file for a single species
#this function has been replaced with reading in json files (see below)
    
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
#function to read a json file for a single species
    with open('./json/'+species+'.json', 'r') as payload:
        mydict = json.load(payload)

    return mydict

def WriteFileJSON(mydict):
#function to write a json file for a single species - need to convert NumPy arrays to lists
    file_uuid = str(uuid.uuid4())
    filename="distillery_"+file_uuid+".json"
    
    output = {'species': mydict['species'],
              'wavelength': list(mydict['wavelength']),
              'n': list(mydict['n']),
              'k': list(mydict['k']),
              'formula': mydict['formula'],
              'density': mydict['density'],
              'temperature': mydict['temperature'],
              'stype' : mydict['stype'],
              'origin' : mydict['origin'],
              'citation': mydict['citation']
              }

    with open('./static/client/'+filename, 'w') as payload:
        json.dump(output, payload)

    return filename

def WriteFileCSV(data):
#function to write a plain txt file based on input data
    file_uuid = str(uuid.uuid4())
    filename='distillery_'+file_uuid+'.csv'
    header  = 'Species: ' + data['species'] + '\n' 
    header += 'Temperature: ' + str(data['temperature']) + '\n' 
    header += 'Density: ' + str(data['density']) + '\n' 
    header += 'Formula: ' + data['formula'] + '\n'
    header += 'Type: ' + data['stype'] + '\n'
    header += 'Origin: ' + data['origin'] +'\n'
    header += 'Citations: ' +  data['citation'] + '\n'
    header += 'Wavelength in microns' + '\n'
    header += '  wav     n      k   ' + '\n'
    header += '#####################'
    np.savetxt('./static/client/'+filename,np.c_[data['wavelength'],data['n'],data['k']],\
               header=header,fmt='%.5f')

    return filename
#
# Here we define the functions that manipulate the optical constants
#
def PlotData(plotdata,title=None,ylog=False,original=None,ylabel=None,labels=None,*args,**kwargs):

  img = io.BytesIO()
         
  plt.title(title)
  plt.plot(plotdata['wavelength'],plotdata['n'],"-k",label=labels[0])
  plt.plot(plotdata['wavelength'],plotdata['k'],"-r",label=labels[1])
  if original != None:
    plt.plot(original['wavelength'],np.asarray(original['n'])+0.05,":k",label=r"$n_{\rm orig} + 0.05$")
    plt.plot(original['wavelength'],np.asarray(original['k'])+0.05,":r",label=r"$k_{\rm orig} + 0.05$")  
  plt.xlabel(r"Wavelength ($\mu$m)")
  plt.ylabel(ylabel)
  #print(form.ylog.data)
  if ylog == True:
      plt.yscale("log")
  plt.xscale("log")
  plt.legend()
  plt.savefig(img, format='svg')
  plt.close()

  return img

def KramersKronig(data_array):

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

def Bruggeman(fracs,input_data):

  data_array = FormatData(input_data)

  wave = data_array[0]['wavelength']
  eps_ = []
  for i in range(0,len(data_array)):
    eps_r = np.asarray(data_array[i]['n'])
    eps_i = np.asarray(data_array[i]['k'])
    elis = []
    for j in range(0,len(wave)):
      elis.append(complex(eps_r[j],eps_i[j]))
    eps_.append(elis)

  eps_ = np.asarray(eps_)

  def BGSolve(eps_bg, epsilons, fracs):
    bg_r,bg_i = eps_bg

    BG = 0.0
    for i in range(0,len(epsilons)):
      BG += np.sum(fracs[i]*((epsilons[i]**2 - complex(bg_r,bg_i)**2)/(epsilons[i]**2 + 2* complex(bg_r,bg_i)**2)))

    return (BG.real, BG.imag)

  initial_guess = [1.5,0.0]
  nn = []
  kk = []
  for j in range(0,len(wave)):
    epsilons = []
    for i in range(0,len(fracs)):
      epsilons.append(eps_[i][j])
    bg_n, bg_k = fsolve(BGSolve, initial_guess, args=(epsilons, fracs))

    nn.append(bg_n)
    kk.append(bg_k)

  return np.asarray(wave),np.asarray(nn),np.asarray(kk)

def MaxwellGarnett(fracs,input_data):

  #format data so the wavelength ranges and sampling match
  data_array = FormatData(input_data)

  #matrix is the larger of the two volume fractions
  wave = data_array[np.argmax(fracs)]['wavelength']
  nm = data_array[np.argmax(fracs)]['n']
  km = data_array[np.argmax(fracs)]['k']

  epsm = []
  for i in range(0,len(nm)):
    epsm.append(complex(nm[i],km[i]))
  epsm = np.asarray(epsm)

  ni = data_array[np.argmin(fracs)]['n']
  ki = data_array[np.argmin(fracs)]['k']

  epsi = []
  for i in range(0,len(ni)):
    epsi.append(complex(ni[i],ki[i]))
  epsi = np.asarray(epsi)

  di = 1. - fracs[np.argmax(fracs)]

  epse = epsm * ( (2*di*(epsi - epsm) + epsi + 2*epsm) / (2*epsm + epsi - di*(epsi - epsm)) )

  mg_n = epse.real
  mg_k = epse.imag

  return np.asarray(wave),mg_n,mg_k

def FormatData(raw_data):

  nspec = len(raw_data)  

  #define grid over which to interpolate species
  wmin = 0.3  #np.min(raw_data[0]['wavelength'])
  wmax = 30.0 #np.max(raw_data[0]['wavelength'])
  nw   = 1000  #len(raw_data[0]['wavelength'])
  wavegrid = np.linspace(wmin,wmax,nw)

  formatted_data = copy.copy(raw_data)

  for i in range(0,len(raw_data)):
    if np.min(raw_data[i]['wavelength']) < wmin or np.max(raw_data[i]['wavelength']) > wmax:
      ex_wav,ex_rl,ex_im = Extrapolation(raw_data[i],wave_min=wmin,wave_max=wmax)

      fn = interp1d(ex_wav,ex_rl)
      formatted_data[i]['n'] = fn(wavegrid)
      fk = interp1d(ex_wav,ex_im)
      formatted_data[i]['k'] = fk(wavegrid)
      formatted_data[i]['wavelength'] = wavegrid

    else: 
      fn = interp1d(raw_data[i]['wavelength'],raw_data[i]['n'])
      formatted_data[i]['n'] = fn(wavegrid)
      fk = interp1d(raw_data[i]['wavelength'],raw_data[i]['k'])
      formatted_data[i]['k'] = fk(wavegrid)
      formatted_data[i]['wavelength'] = wavegrid
  
  return formatted_data


def OpTool(commands):
  """Function to combine and extrapolate optical constants for materials using optool
  """

  wmin = commands['wmin']
  wmax = commands['wmax']
  wave_string = " -l "+str(wmin)+" "+str(wmax)+" -fmax 0"


  methodrule = commands['methodrule']
  monomer = commands['monomer']
  fmax = commands['fillfac']
  if methodrule == 'Distribution of Hollow Spheres':
    meth_string = ' -dhs '+str(fmax)+' '
  elif methodrule == 'Modified Mean Field':
    meth_string = ' -mmf '+str(monomer)+' '+str(fmax)+' '
  elif methodrule == 'Mie':
    meth_string = ' -mie ' # == -dhs 0 
  elif methodrule == 'Continuous Distribution of Ellipsoids':
    meth_string = ' -cde '
  else:
    print("Method rule not known")

  distrirule = commands['distrirule']
  amin = commands['amin']
  amax = commands['amax']
  if distrirule == 'Power Law':
    apow = commands['apow']
    dist_string = '-a '+str(amin)+' '+str(amax)+' '+str(apow)+' '
  elif distrirule == 'Log-Normal':
    apek = commands['apow']
    asig = commands['asig']
    dist_string = '-a '+str(amin)+' '+str(amax)+' '+str(apek)+' '+str(asig)+' '
  else: 
    print("Distribution rule not known")

  #Execute optool command
  composition = commands['direc']+commands['optc1'] +' '+str(commands['frac1'])+' '+str(commands['rho1'])+' '+commands['direc']+commands['optc2'] +' '+str(commands['frac2'])+' '+' '+str(commands['rho2'])+' '
  
  print("optool "+composition+ meth_string+ dist_string+ wave_string)

  #os.system("optool "+composition+ meth_string+ dist_string+ wave_string)
  out = subprocess.Popen("optool " +composition+ meth_string+ dist_string+ wave_string, shell=True).wait()

  #Read in dustkappa.dat
  optconst = ascii.read("dustkappa.dat",comment="#",data_start=2) 

  wavelength = optconst["col1"].data
  qabs = optconst["col2"].data
  qsca = optconst["col3"].data

  return wavelength, qabs, qsca

def Extrapolation(species,wave_min=0.1,wave_max=1000.0,nlow=100,nhigh=100,logspace=True):
  """Function to extrapolate given realities to cover the full range of
     a common, uniform wavelength grid."""

  wave = species['wavelength']
  real = species['n']
  imag = species['k']

  if wave_min > np.min(wave) and wave_max < np.max(wave):
      print(species['species']," reality spectrum within bounds, no extrapolation required.")
      extrap_wave, extrap_real, extrap_imag = wave, real, imag

  elif wave_min < np.min(wave) and wave_max > np.max(wave):
      print("Extrapolating to both shorter and longer wavelengths")

      #short wavelength part
      if logspace == True :
        extra_wave_lo = np.logspace(np.log10(0.9*wave_min),np.log10(wave[0]),num=nlow,base=10.0,endpoint=True)
      else: 
        extra_wave_lo = np.linspace(0.9*wave_min,wave[0],num=nlow)

      slope_real_lo = (real[1] - real[0]) / (wave[1] - wave[0])
      extra_real_lo = real[0] + (slope_real_lo * (extra_wave_lo - wave[0]))

      slope_imag_lo = (imag[1] - imag[0]) / (wave[1] - wave[0])
      extra_imag_lo = imag[0] + (slope_imag_lo * (extra_wave_lo - wave[0]))

      #long wavelength part
      if logspace == True :
        extra_wave_hi = np.logspace(np.log10(wave[-1]),np.log10(1.1*wave_max),num=nhigh,base=10.0,endpoint=True)
      else: 
        extra_wave_hi = np.linspace(wave[-1],1.1*wave_max,num=nhigh)

      slope_real_hi = (real[-2] - real[-1]) / (wave[-2] - wave[-1])
      extra_real_hi = real[-1] + (slope_real_hi * (extra_wave_hi - wave[-1]))

      slope_imag_hi = (imag[-2] - imag[-1]) / (wave[-2] - wave[-1])
      extra_imag_hi = imag[-1] + (slope_imag_hi * (extra_wave_hi - wave[-1]))

      #stitch it all together (have to do this piecewise)
      wave_mid = np.append(extra_wave_lo,wave[1:])
      real_mid = np.append(extra_real_lo,real[1:])
      imag_mid = np.append(extra_imag_lo,imag[1:])
      
      extrap_wave = np.append(wave_mid,extra_wave_hi[1:])
      extrap_real = np.append(real_mid,extra_real_hi[1:])
      extrap_imag = np.append(imag_mid,extra_imag_hi[1:])

  elif wave_min < np.min(wave) and wave_max <= np.max(wave):
      print("Extrapolating to shorter wavelengths")

      if logspace == True : 
        extra_wave = np.logspace(np.log10(0.9*wave_min),np.log10(wave[0]),num=nlow,base=10.0,endpoint=True)
      else: 
        extra_wave = np.linspace(0.9*wave_min,wave[0],num=nlow)

      slope_real = (real[1] - real[0]) / (wave[1] - wave[0])
      extra_real = real[0] + (slope_real * (extra_wave - wave[0]))

      slope_imag = (imag[1] - imag[0]) / (wave[1] - wave[0])
      extra_imag = imag[0] + (slope_imag * (extra_wave - wave[0]))

      extrap_wave = np.append(extra_wave,wave[1:])
      extrap_real = np.append(extra_real,real[1:])
      extrap_imag = np.append(extra_imag,imag[1:])
  
  elif wave_max > np.max(wave) and wave_min >= np.min(wave): 
      print("Extrapolating to longer wavelengths")

      if logspace == True :
        extra_wave = np.logspace(np.log10(wave[-1]),np.log10(1.1*wave_max),num=nhigh,base=10.0,endpoint=True)
      else: 
        extra_wave = np.linspace(wave[-1],1.1*wave_max,num=nhigh)
      
      slope_real = (real[-2] - real[-1]) / (wave[-2] - wave[-1])
      extra_real = real[-1] + (slope_real * (extra_wave - wave[-1]))

      slope_imag = (imag[-2] - imag[-1]) / (wave[-2] - wave[-1])
      extra_imag = imag[-1] + (slope_imag * (wave[-1] - extra_wave))

      extrap_wave = np.append(wave,extra_wave[1:])
      extrap_real = np.append(real,extra_real[1:])
      extrap_imag = np.append(imag,extra_imag[1:])
      
  return extrap_wave, extrap_real, extrap_imag

