import numpy as np
import json
import pyodbc

#To do list:
# Support plotting
# Support Flask + Plotly for dynamic website
# Implement SQL database interaction (creation, read, write)
# Implement sanity checks on files (both info and lnk present in directory)
# Implement sanity checks on database (is a species with same name already in there)
# Implement calculation of optical constants/Qabs/dielectric functions from given values

def ReadData(species=None):
#function to read in a formatted text file for a single species
    
    # lnk file has 3 columns, space delimited
    # wavelength (um), n, k
    with open('data/'+species+'.lnk', 'r') as f:
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
    with open('data/'+species+'.info', 'r') as f:
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
    with open('json/'+species+'.json', 'r') as payload:
        mydict = json.load(payload)

    return mydict

def WriteJSON(mydict):
#function to write a json file for a single species
    with open('json/'+mydict['species']+'.json', 'w') as payload:
        json.dump(mydict, payload)

def CreateSQL(server='localhost',port='1433',database='OpticalConstants',username='user',password='password'):
#function to create a database
    config = dict(server='localhost',port=1433,database=database,username=username,password= password)

    conn = pyodbc.connect("driver={SQL Server};server={server}; port={port}; database={database}; username={username}; password={password}",
                          autocommit=True)

def WriteSQL(dbname):
#function to add an entry to a database for a single species
    print("Not yet implemented")

def MixSpecies(species1,species2,ratio=0.5):
#function to mix optical constants from two (or more) species with a given ratio
    print("Not yet implemented")

def ConvertWavenumber(wavenumber):
#function to convert wavenumber cm^-1 into wavelength um

    wavelength = 1e-4 / wavenumber

    return wavelength

def ConvertOC(input=None,conversion='nk2bs'):
#function to convert input to/from n,k into something else

#Assuming mu = 1 (true for non-magnetic materials at optical wavelengths)
#dielectric: e_real = n**2 - k**2
#            e_imag = 2*n*k
#            e_real + i e_imag = (n + i k)**2
    print("Not yet implemented")