import numpy as np
import json
import mysql

class JWST_Optical_Constants(self):

    def Create(self,dbname,dbpass):
    #function to create a database

    def Read(self,species=None):
    #function to read in a formatted text file for a single species
        lnk_table = ascii.read(species+'.lnk',guess=False)
        l = lnk_table[0]
        n = lnk_table[1]
        k = lnk_table[2]

        f = open(species+'.txt', 'r')

        info_table = f.readlines()
        for line in info_table:
            line.strip()

        mydict = {'species': info_table[0],
                  'citation': info_table[1],
                  'wavelength': l,
                  'n': n,
                  'k': k,
                  'temperature': info_table[2],
                  'density': info_table[3],
                  'formula': info_table[4],
                  'origin' : info_table[5],
                  'stype' : info_table[6],
                  }

        return mydict

    def Write_JSON(self,mydict):
    #function to write a json file for a single species
    with open(mydict['species']+'.json', 'w') as output:
        json.dump(mydict, output)

    def Write_SQL(self,dbname):
    #function to add an entry to a database for a single species