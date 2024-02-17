from flask import render_template, Flask,send_file,request,Response,url_for,send_from_directory
from wtforms import Form, FloatField, validators,BooleanField,SelectField,SelectMultipleField
import io
import base64
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import matplotlib.pyplot as plt
import glob
import json
import os

import distillery #functions to manipulate optical constants - everything not webpage related.

#@app.route("/myplot", methods=["GET"])
matplotlib.use('Agg')

#
# Here we define the input forms for each page on the site
#
class PlotForm(Form):
    optcons=glob.glob("./static/opticalconstants/json/*")
    optcons.sort()
    listopt=[]
    for i_optcon,optcon in enumerate(optcons):
        listopt.append((i_optcon,optcon.split("/")[-1].strip('.json')))
    print(listopt)
   
    optc=SelectField("Species",choices=listopt)
    savedata= BooleanField(label="Make raw data available for download",render_kw={'checked': False})
    ylog= BooleanField(label="Log Y-axis",default="")


class ExtrapolateForm(Form):
    optcons=glob.glob("./static/opticalconstants/json/*")
    optcons.sort()
    listopt=[]
    for i_optcon,optcon in enumerate(optcons):
        listopt.append((i_optcon,optcon.split("/")[-1].strip('.json')))
    print(listopt)
    
    optc=SelectField("Species",choices=listopt)
    #options_sil=SelectMultipleField("Select Silicates (unused)",choices=listopt)
    #options_car=SelectMultipleField("Select Carbons (unused)",choices=listopt)
    #options_ice=SelectMultipleField("Select Ices (unused)",choices=listopt)
    wmin=FloatField(label="Shortest wavelength for extrapolated values (um)", default=0.1,validators=[validators.NumberRange(min=0.01,max=10000,message="Number outside of bounds 0.01<=f<=10000")])
    wmax=FloatField(label="Longest wavelength for extrapolated values (um)", default=1000.0,validators=[validators.NumberRange(min=0.01,max=10000,message="Number outside of bounds 0.01<=f<=10000")])   
    nlong=FloatField(label="Number of extrapolated data points at longer wavelengths", default=100,validators=[validators.NumberRange(min=2,max=1000,message="Number outside of bounds 2<=f<=1000")])
    nshort=FloatField(label="Number of extrapolated data points at shorter wavelengths", default=100,validators=[validators.NumberRange(min=2,max=1000,message="Number outside of bounds 2<=f<=1000")])    
    exlog= BooleanField(label="Extrapolate in Log space",default="")
    savedata= BooleanField(label="Make raw data available for download",render_kw={'checked': False})
    ylog= BooleanField(label="Log Y-axis",default="")


class MixingForm(Form):
    optcons=glob.glob("./static/opticalconstants/json/*")
    optcons.sort()
    listopt=[]
    for i_optcon,optcon in enumerate(optcons):
        listopt.append((i_optcon,optcon.split("/")[-1].strip('.json')))
    #print(listopt)
    listmix = ['Bruggeman','MaxwellGarnett']
    optc1=SelectField("1st Species",choices=listopt)
    frac1=FloatField(label="Fraction", default=0.5,validators=[validators.NumberRange(min=0,max=1,message="Fraction outside of bounds 0<=f<=1")])
    optc2=SelectField("2nd Species",choices=listopt,default=2)
    frac2=FloatField(label="Fraction", default=0.5,validators=[validators.NumberRange(min=0,max=1,message="Fraction outside of bounds 0<=f<=1")])
    optc3=SelectField("3rd Species",choices=listopt,default=3)
    frac3=FloatField(label="Fraction", default=0.0,validators=[validators.NumberRange(min=0,max=1,message="Fraction outside of bounds 0<=f<=1")])
    mixrule=SelectField("Mixing Rule",choices=listmix)
    savedata= BooleanField(label="Make output data available for download",render_kw={'checked': True})
    ylog= BooleanField(label="Log Y-axis",default="")


class MixingOpToolForm(Form):
    optcons=glob.glob("./static/opticalconstants/lnk/*")
    optcons.sort()
    listopt=[]
    for i_optcon,optcon in enumerate(optcons):
        listopt.append((i_optcon,optcon.split("/")[-1].strip('.lnk')))
    #print(listopt)
    listmethod = ['Distribution of Hollow Spheres','Modified Mean Field','Mie','Continuous Distribution of Ellipsoids']
    listdistri = ['Power Law','Log-Normal']
    
    wmin=FloatField(label="Shortest wavelength for extrapolated values (um)", default=0.1,validators=[validators.NumberRange(min=0.01,max=10000,message="Number outside of bounds 0.01<=f<=10000")])
    wmax=FloatField(label="Longest wavelength for extrapolated values (um)", default=1000.0,validators=[validators.NumberRange(min=0.01,max=10000,message="Number outside of bounds 0.01<=f<=10000")])   

    optc1=SelectField("1st Species",choices=listopt)
    frac1=FloatField(label="Fraction", default=0.5,validators=[validators.NumberRange(min=0,max=1,message="Fraction outside of bounds 0<=f<=1")])
    optc2=SelectField("2nd Species",choices=listopt,default=2)
    frac2=FloatField(label="Fraction", default=0.5,validators=[validators.NumberRange(min=0,max=1,message="Fraction outside of bounds 0<=f<=1")])
    
    methodrule = SelectField("Grain geometry:",choices=listmethod)
    
    monomer = FloatField(label="Monomer size (um)", default=0.1,validators=[validators.NumberRange(min=0,max=1,message="Value outside of bounds 0<=f<=1")])
    fillfac = FloatField(label="Fill Fraction", default=0.5,validators=[validators.NumberRange(min=0,max=1,message="Value outside of bounds 0<=f<=1")])

    distrirule = SelectField("Size distribution",choices=listdistri)

    amin = FloatField(label="Minimum size (um)", default=0.1,validators=[validators.NumberRange(min=1e-3,max=1e6,message="Value outside of bounds 1e-3 to 1e6")])
    amax = FloatField(label="Maximum size (um)", default=1e3,validators=[validators.NumberRange(min=1e-3,max=1e6,message="Value outside of bounds 1e-3 to 1e6")])
    apow = FloatField(label="Power law exponent/Peak of sizes (um)*", default=3.5,validators=[validators.NumberRange(min=1e-3,max=1e6,message="Value outside of bounds 1e-3 to 1e6")])
    asig = FloatField(label="Standard deviation of sizes (um)*", default=0.5,validators=[validators.NumberRange(min=1e-3,max=1e6,message="Value outside of bounds 1e-3 to 1e6")])

    savedata= BooleanField(label="Make output data available for download",render_kw={'checked': True})
    ylog= BooleanField(label="Log Y-axis",default="")

def extend():
    print("Not yet implemented!")

#
# Here we start the app!
#

app = Flask(__name__)

import datetime

import base64

@app.route("/favicon.ico")
def favicon():
    return send_from_directory('./static',"favicon_wisci.png",mimetype = 'image/vnd.microsoft.icon')
#@context.processor


#@app.route('/data/<file_name>') # this is a route that directly serves a generated file and is available from the outside through 127.0.0.1:5000/data/blabla which will return a file blabla.csv
#def get_file(file_name):
    #def generate_csv_file():
        #file_buffer=io.StringIO()
        #np.savetxt(file_buffer,np.c_[np.arange(10),np.arange(10)+10])
        #file_buffer.seek(0)
        #return file_buffer
    #generated_file=generate_csv_file()
    #response=Response(generated_file,mimetype="text/csv")
    #response.headers.set("Content-Disposition","attachment",filename="{0}.csv".format(file_name))
    #return response

#
# Here we define the machinery of each page on the site
#

@app.route("/get-data/<path:name>")
def download_file(name):
    return send_from_directory("./static/client/", name, as_attachment=True)

@app.route('/plot',methods=['GET','POST'])
def plot():
    if True:
    #try:
        form=PlotForm(request.form)
        if request.method == 'POST' and form.validate():
            optcons=glob.glob("./static/opticalconstants/json/*")
            optcons.sort()
            #print("form data?",np.int32(form.optc.data))
            #print(optcons[np.int32(form.optc.data)])
            #arr1,arr2,arr3=np.loadtxt(optcons[np.int32(form.optc.data)],unpack=1)
            
            with open(optcons[np.int32(form.optc.data)]) as datafile:
                data  = json.load(datafile)


            # magic data reduction and calculations take place here

            img = distillery.PlotData(data,title=optcons[np.int32(form.optc.data)].split("/")[-1].split(".")[0],ylabel="Refractive indices $n$,$k$",labels=["$n$","$k$"],ylog=form.ylog.data)
            img.seek(0)

            plot_url = base64.b64encode(img.getvalue()).decode('utf8')

            if form.savedata.data == True:
                filename = distillery.WriteFileJSON(data)
            else:
                filename=None
            return render_template('plot.html', plot_url=plot_url,form=form,
                                    values=data,
                                    filename=filename)
        else:
            plot_url=None
            filename=None
            data=None
            return render_template('plot.html', plot_url=plot_url,form=form,
                                    values=data,
                                    filename=filename)
#except:
     #   return render_template('err.html')

#Plot up a set of optical constants
@app.route('/extrapolate',methods=['GET','POST'])
def extrapolate():
    if True:
    #try:
        form=ExtrapolateForm(request.form)
        if request.method == 'POST' and form.validate():
            optcons=glob.glob("./static/opticalconstants/json/*")
            optcons.sort()
            
            with open(optcons[np.int32(form.optc.data)]) as datafile:
                data  = json.load(datafile)

            # magic data reduction and calculations take place here
            if form.exlog.data == False :
                kind = 'linear'
            else:
                kind = 'log'

            extra_w, extra_n, extra_k = distillery.Extrapolation(data,wave_min=form.wmin.data,wave_max=form.wmax.data,
                                                                nlow=int(form.nlong.data),nhigh=int(form.nshort.data),logspace=form.exlog.data)

            #create dictionary object for extrapolation species
            extrapolate_data = {'species' : 'extrapolation: '+ data['species'],
                       'formula' : data['formula'],
                       'wavelength' : extra_w,
                       'n' : extra_n,
                       'k' : extra_k, 
                       'density' : data['density'],
                       'temperature' : data['temperature'],
                       'stype' : data['stype'],
                       'origin' : 'CALCULATION',
                       'citation' : 'WISCI Distillery ; '+data['citation'] }

            img = distillery.PlotData(extrapolate_data,title=optcons[np.int32(form.optc.data)].split("/")[-1].split(".")[0],ylog=form.ylog.data,ylabel="Refractive indices $n$,$k$",labels=[r"$n_{\rm extr}$",r"$k_{\rm extr}$"],original=data)
            img.seek(0)

            extrapolate_plot = base64.b64encode(img.getvalue()).decode('utf8')
            filename = None
            if form.savedata.data == True:
                filename = distillery.WriteFileJSON(extrapolate_data)
            message = None
            return render_template('extrapolate.html', extrapolate_plot=extrapolate_plot,form=form,
                                    values=extrapolate_data,message=message,
                                    filename=filename)
        else:
            extrapolate_plot=None
            extrapolate_data=None
            filename=None
            message=None
            return render_template('extrapolate.html', plot_url=extrapolate_plot,form=form,
                                    values=extrapolate_data,message=message,
                                    filename=filename)

#Mix two or three sets of optical constants together
@app.route('/mixing',methods=['GET','POST'])
def mixing():
    if True:
    #try:
        form=MixingForm(request.form)
        if request.method == 'POST' and form.validate():
            optcons=glob.glob( "./static/opticalconstants/json/*")
            optcons.sort()
            
            #sort out which species and how many in what order:
            if np.sum(form.frac1.data + form.frac2.data + form.frac3.data) == 0.0 :
                return render_template('err.html',page='Mixing',error="Sum of fractions cannot be zero.")

            if np.sum(form.frac1.data + form.frac2.data + form.frac3.data) != 1.0 : #normalise to unity
                frac_sum = form.frac1.data + form.frac2.data + form.frac3.data
                form.frac1.data /= frac_sum
                form.frac2.data /= frac_sum
                form.frac3.data /= frac_sum

            if form.frac1.data == 0.0:
                return render_template('err.html',page='Mixing',error="First species fraction cannot be zero.")

            data_array = []
            species = []
            fracs = []
            with open(optcons[np.int32(form.optc1.data)]) as datafile:
                data_array.append(json.load(datafile))
                species.append(optcons[np.int32(form.optc1.data)].split("/")[-1].split(".")[0])
                fracs.append(form.frac1.data)

            if form.frac2.data != 0.0:
                with open(optcons[np.int32(form.optc2.data)]) as datafile:
                    data_array.append(json.load(datafile))
                    species.append(optcons[np.int32(form.optc2.data)].split("/")[-1].split(".")[0])
                    fracs.append(form.frac2.data)

            if form.frac3.data != 0.0: 
                with open(optcons[np.int32(form.optc3.data)]) as datafile:
                    data_array.append(json.load(datafile))
                    species.append(optcons[np.int32(form.optc3.data)].split("/")[-1].split(".")[0])
                    fracs.append(form.frac3.data)

            nspecies = len(data_array)
            # magic data reduction and calculations take place here
            plot_urls=[]

            density = 0.0
            composition_string = ''
            mixture_string     = ''
            stype_string       = ''
            citation_string    = '' 
            for i in range(0,nspecies):
                data = data_array[i]
                composition_string += str(fracs[i])+'x '+data['species']+', '
                mixture_string     += data['formula'] + ', '
                stype_string       += data['stype'] + ', '
                citation_string    += data['citation'] + '; '

                data = data_array[i]
                density += data['density']*fracs[i]

                img = distillery.PlotData(data,title=species[i],ylog=form.ylog.data,ylabel='Refractive indices $n$,$k$',labels=[r'$n_{\rm mix}$',r'$k_{\rm mix}$'])
                img.seek(0)

                plot_urls.append(base64.b64encode(img.getvalue()).decode('utf8'))

            print(form.mixrule.data)
            if form.mixrule.data == 'Bruggeman' :
                out_l,out_n,out_k = distillery.Bruggeman(fracs,data_array)

            elif form.mixrule.data == 'MaxwellGarnett' :
                out_l,out_n,out_k = distillery.MaxwellGarnett(fracs,data_array)

            #create dictionary object for mixture species
            mixture = {'species' : 'mixture: '+composition_string,
                       'formula' : 'mixture: '+mixture_string,
                       'wavelength' : out_l,
                       'n' : out_n,
                       'k' : out_k, 
                       'density' : str(density),
                       'temperature' : 'N/A',
                       'stype' : 'mixture: '+stype_string,
                       'origin' : 'CALCULATION',
                       'citation' : 'WISCI Distillery ; '+citation_string}

            #plot for mixture
            img = distillery.PlotData(mixture,title="mixture: "+composition_string,ylog=form.ylog.data,ylabel='Refractive indices $n$,$k$',labels=[r'$n_{\rm mix}$',r'$k_{\rm mix}$'])
            img.seek(0)
            plot_mixture = base64.b64encode(img.getvalue()).decode('utf8')

            if form.savedata.data == True:
                filename = distillery.WriteFileJSON(mixture)
            else: 
                filename=None
            return render_template('mixing.html', plot_urls=plot_urls,form=form,
                                    values=data_array,mixture=mixture,plot_urlm=plot_mixture,
                                    filename=filename)

        else:
            plot_urls=None
            filename=None
            data_array=None
            mixture=None
            plot_mixture=None
            return render_template('mixing.html', plot_urls=plot_urls,form=form,
                                    values=data_array,mixture=mixture,plot_urlm=plot_mixture,
                                    filename=filename)

#Caclulate Qabs, Qsca for material using optical constants
@app.route('/calculating',methods=['GET','POST'])
def calculating():
    if True:
    #try:
        form=MixingOpToolForm(request.form)
        if request.method == 'POST' and form.validate():
            optcons=glob.glob("./static/opticalconstants/lnk/*.lnk")
            optcons.sort()
            
            #sort out which species and how many in what order:
            if np.sum(form.frac1.data + form.frac2.data) == 0.0 :
                return render_template('err.html',page='Mixing',error="Sum of fractions cannot be zero.")

            if form.frac1.data == 0.0:
                return render_template('err.html',page='Mixing',error="First species fraction cannot be zero.")

            #load json files with ancillary information
            with open('./static/opticalconstants/json/'+optcons[np.int32(form.optc1.data)].split('/')[-1].strip('.lnk')+'.json') as datafile:
                data1  = json.load(datafile)
            with open('./static/opticalconstants/json/'+optcons[np.int32(form.optc2.data)].split('/')[-1].strip('.lnk')+'.json')  as datafile:
                data2  = json.load(datafile)

            data_array = [data1,data2]

            #check if lnk files for these compositions exist; if not, make them
            #lnkpaths = []
            #for i in range(0,len(data_array)):
            #    data = data_array[i]
            #    lnkpaths.append('./static/opticalconstants/lnk/'+data["species"]+'.lnk')
            
            for i in range(0,len(data_array)):
                data    = data_array[i]                
                lnkfile = './static/opticalconstants/lnk/'+ data["species"]+'.lnk'

                try:
                    os.path.isfile(lnkfile)
                    print(lnkfile + " exists")
                except FileNotFoundError:
                    print(lnkfile + " does not exist, writing .lnk file")
                    np.savetxt(lnkfile,np.c_[data['wavelength'],data['n'],data['k']])

            optool_inputs = {'direc':"./static/opticalconstants/lnk/",
                             'wmin':form.wmin.data,
                             'wmax':form.wmax.data,
                             'optc1':'./static/opticalconstants/lnk/'+ data1["species"]+'.lnk',
                             'frac1':form.frac1.data,
                             'rho1':data1['density'],
                             'optc2':'./static/opticalconstants/lnk/'+ data2["species"]+'.lnk',
                             'frac2':form.frac2.data,
                             'rho2':data2['density'],
                             'methodrule':form.methodrule.data,
                             'monomer':form.monomer.data,
                             'fillfac':form.fillfac.data,
                             'distrirule':form.distrirule.data,
                             'amin':form.amin.data,
                             'amax':form.amax.data,
                             'apow':form.apow.data,
                             'asig':form.asig.data}
            print(optool_inputs)

            out_l,out_n,out_k = distillery.OpTool(optool_inputs)

            density = 0.0
            composition_string = ''
            mixture_string     = ''
            stype_string       = ''
            citation_string    = ''
            for i in range(0,nspecies):
                data = data_array[i]
                density += data['density']*fracs[i]

                if i != npsecies-1:
                    composition_string += data['species'] + ' , ' 
                    mixture_string     += data['formula'] + ' , '
                    stype_string       += data['stype'] + ' , ' 
                    citation_string    += data['citation'] + '; '
                else:
                    composition_string += data['species']
                    mixture_string     += data['formula']
                    stype_string       += data['stype']
                    citation_string    += data['citation']

            #create dictionary object for mixture species
            mixture = {'species' : 'mixture: '+composition_string,
                       'formula' : 'mixture: '+mixture_string, 
                       'wavelength' : out_l,
                       'n' : out_n,
                       'k' : out_k, 
                       'density' : str(density),
                       'temperature' : 'N/A',
                       'stype' : stype_string,
                       'origin' : 'CALCULATION',
                       'citation' : 'WISCI Distillery ; ' +citation_string }

            #plot for mixture
            plot_urls=None
            data_array = []
            img = distillery.PlotData(mixture,title="mixture: "+composition_string,ylabel="Qabs, Qsca",labels=["Qabs","Qsca"],ylog=form.ylog.data)
            img.seek(0)
            plot_mixture = base64.b64encode(img.getvalue()).decode('utf8')

            if form.savedata.data == True:
                filename = distillery.WriteFileJSON(mixture)
            else: 
                filename=None
            return render_template('calculating.html', plot_urls=plot_urls,form=form,
                                    values=data_array,mixture=mixture,plot_urlm=plot_mixture,
                                    filename=filename)

        else:
            plot_urls=None
            filename=None
            data_array=None
            mixture=None
            plot_mixture=None
            return render_template('calculating.html', plot_urls=plot_urls,form=form,
                                    values=data_array,mixture=mixture,plot_urlm=plot_mixture,
                                    filename=filename)

app.run(debug=True)
