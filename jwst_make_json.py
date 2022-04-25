import jwst_optical_constants as joc
import glob

optcons=glob.glob("./data/*.lnk")
for i in range(0,len(optcons)):
	species = optcons[i].split("/")[-1].split(".")[0]
	print(species)
	mydict = joc.ReadData(species=species)

	joc.WriteJSON(mydict)
