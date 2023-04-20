import distillery
import glob 

species_list=glob.glob("data/*")
species_list.sort() 

for i in range(0,len(species_list)):
	species = species_list[i].split("/")[-1].split(".")[0]
	mydict = distillery.ReadData(species=species)
	distillery.WriteJSON(mydict)