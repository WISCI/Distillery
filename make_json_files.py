import distillery
import glob 
import json

species_list=glob.glob("data/*")
species_list.sort() 

for i in range(0,len(species_list)):
	species = species_list[i].split("/")[-1].split(".")[0]
	mydict = distillery.ReadData(species=species)
	
	try:
		mydict['wavelength'].tolist()
		mydict['n'].tolist()
		mydict['k'].tolist()
	except:
		pass
    
	output = {'species': mydict['species'],
				'wavelength': mydict['wavelength'],
				'n': mydict['n'],
				'k': mydict['k'],
				'formula': mydict['formula'],
				'density': mydict['density'],
				'temperature': mydict['temperature'],
				'stype' : mydict['stype'],
				'origin' : mydict['origin'],
				'citation': mydict['citation']
				}

	with open('./'+species_list[i].split(".")[0]+'.json', 'w') as payload:
		json.dump(output, payload)