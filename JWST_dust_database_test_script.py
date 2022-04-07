import jwst_optical_constants as joc

mydict = joc.ReadData(species='pyrmg70')

#joc.WriteJSON(mydict)
#mydict2 = joc.ReadJSON(species='pyrmg70')

joc.CreateSQL()