from flask import render_template, Flask,send_file,request,Response,url_for,send_from_directory
from wtforms import Form, FloatField, validators,BooleanField,SelectField,SelectMultipleField
import io
import base64
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import uuid
import matplotlib.pyplot as plt
import glob
import json
import os
import scipy.interpolate as intp
from scipy import integrate
import scipy.fftpack as ft
#@app.route("/myplot", methods=["GET"])
matplotlib.use('Agg')



#
# Here we define the input forms for each page on the site
#
class PlotForm(Form):
    optcons=glob.glob("./static/opticalconstants/*")
    optcons.sort()
    listopt=[]
    for i_optcon,optcon in enumerate(optcons):
        listopt.append((i_optcon,optcon.split("/")[-1].split(".")[0]))
    print(listopt)
   
    optc=SelectField("Species",choices=listopt)
    options_sil=SelectMultipleField("Select Silicates (unused)",choices=listopt)
    options_car=SelectMultipleField("Select Carbons (unused)",choices=listopt)
    options_ice=SelectMultipleField("Select Ices (unused)",choices=listopt)
    savedata= BooleanField(label="Make raw data available for download",render_kw={'checked': False})
    ylog= BooleanField(label="Log Y-axis",default="")


class ExtrapolateForm(Form):
    optcons=glob.glob("./static/opticalconstants/*")
    optcons.sort()
    listopt=[]
    for i_optcon,optcon in enumerate(optcons):
        listopt.append((i_optcon,optcon.split("/")[-1].split(".")[0]))
    print(listopt)
    
    optc=SelectField("Species",choices=listopt)
    options_sil=SelectMultipleField("Select Silicates (unused)",choices=listopt)
    options_car=SelectMultipleField("Select Carbons (unused)",choices=listopt)
    options_ice=SelectMultipleField("Select Ices (unused)",choices=listopt)
    savedata= BooleanField(label="Make raw data available for download",render_kw={'checked': False})
    ylog= BooleanField(label="Log Y-axis",default="")


class MixingForm(Form):
    optcons=glob.glob("./static/opticalconstants/*")
    optcons.sort()
    listopt=[]
    for i_optcon,optcon in enumerate(optcons):
        listopt.append((i_optcon,optcon.split("/")[-1].split(".")[0]))
    #Add vacuum to list of choices for porosity calculations
    listopt.append((i_optcon+1,'vacuum'))
    print(listopt)
    
    optc1=SelectField("1st Species",choices=listopt)
    frac1=FloatField(label="Fraction", default=1.0,validators=[validators.NumberRange(min=0,max=1,message="Fraction outside of bounds 0<=f<=1")])
    optc2=SelectField("2nd Species",choices=listopt)
    frac2=FloatField(label="Fraction", default=0.0,validators=[validators.NumberRange(min=0,max=1,message="Fraction outside of bounds 0<=f<=1")])
    optc3=SelectField("3rd Species",choices=listopt)
    frac3=FloatField(label="Fraction", default=0.0,validators=[validators.NumberRange(min=0,max=1,message="Fraction outside of bounds 0<=f<=1")])
    savedata= BooleanField(label="Make output data available for download",render_kw={'checked': True})
    ylog= BooleanField(label="Log Y-axis",default="")


#
# Here we define the functions that manipulate the optical constants
#
def kramers_kronig(data_array):

    for i in range(0,len(data_array)):

        data = data_array[i]

        if i == 0:
            kk_l = np.asarray(data['wavelength'])
            kk_n = np.asarray(data['n'])
            kk_k = np.asarray(data['k'])
        else:
            kk_n = 1/len(data_array)*(np.asarray(data['n'])) + 1.
            kk_k = 1/len(data_array)*(kk_k + np.asarray(data['k']))
        

    return kk_l,kk_n, kk_k


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
            optcons=glob.glob("./static/opticalconstants/*")
            optcons.sort()
            #print("form data?",np.int32(form.optc.data))
            #print(optcons[np.int32(form.optc.data)])
            #arr1,arr2,arr3=np.loadtxt(optcons[np.int32(form.optc.data)],unpack=1)
            
            with open(optcons[np.int32(form.optc.data)]) as datafile:
                data  = json.load(datafile)


            # magic data reduction and calculations take place here

            img = io.BytesIO()
    
            x = np.arange(10)
            plt.title("somebodys_plot "+str(datetime.date.today())+" "+optcons[np.int32(form.optc.data)].split("/")[-1].split(".")[0])
            plt.plot(data['wavelength'],data['n'],"-k",label="$n$")
            plt.plot(data['wavelength'],data['k'],"-r",label="$k$")
            plt.xlabel(r"Wavelength ($\mu$m)")
            plt.ylabel(r"Refractive indices $n$,$k$")
            #print(form.ylog.data)
            if form.ylog.data == True:
                plt.yscale("log")
            plt.xscale("log")
            plt.legend()
            plt.savefig(img, format='svg')
            plt.close()
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode('utf8')

            if form.savedata.data == True:
                file_uuid = str(uuid.uuid4())
                filename="distillery_"+file_uuid+".csv"
                np.savetxt("./static/client/"+filename,np.c_[data['wavelength'],data['n'],data['k']])
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

@app.route('/extrapolate',methods=['GET','POST'])
def extrapolate():
    if True:
    #try:
        form=ExtrapolateForm(request.form)
        if request.method == 'POST' and form.validate():
            optcons=glob.glob("./static/opticalconstants/*")
            optcons.sort()
            
            with open(optcons[np.int32(form.optc.data)]) as datafile:
                data  = json.load(datafile)


            # magic data reduction and calculations take place here

            img = io.BytesIO()
    
            x = np.arange(10)
            plt.title("somebodys_plot "+str(datetime.date.today())+" "+optcons[np.int32(form.optc.data)].split("/")[-1].split(".")[0])
            plt.plot(data['wavelength'],data['n'],"-k",label="$n$")
            plt.plot(data['wavelength'],data['k'],"-r",label="$k$")
            plt.xlabel(r"Wavelength ($\mu$m)")
            plt.ylabel(r"Refractive indices $n$,$k$")
            #print(form.ylog.data)
            if form.ylog.data == True:
                plt.yscale("log")
            plt.xscale("log")
            plt.legend()
            plt.savefig(img, format='svg')
            plt.close()
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode('utf8')

            if form.savedata.data == True:
                file_uuid = str(uuid.uuid4())
                filename="distillery_"+file_uuid+".csv"
                np.savetxt("./static/client/"+filename,np.c_[data['wavelength'],data['n'],data['k']])
            else:
                filename=None
            return render_template('extrapolate.html', plot_url=plot_url,form=form,
                                    values=data,
                                    filename=filename)
        else:
            plot_url=None
            filename=None
            data=None
            return render_template('extrapolate.html', plot_url=plot_url,form=form,
                                    values=data,
                                    filename=filename)

@app.route('/mixing',methods=['GET','POST'])
def mixing():
    if True:
    #try:
        form=MixingForm(request.form)
        if request.method == 'POST' and form.validate():
            optcons=glob.glob("./static/opticalconstants/*")
            optcons.sort()
            
            #sort out which species and how many in what order:
            if np.sum(form.frac1.data + form.frac2.data + form.frac3.data) == 0.0 :
                return render_template('err.html',page='Mixing',error="Sum of fractions cannot be zero.")

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
            for i in range(0,nspecies):
                data = data_array[i]
                density += data['density']*fracs[i]

                img = io.BytesIO()
    
                x = np.arange(10)
                plt.title("somebodys_plot "+str(datetime.date.today())+" "+species[i])
                plt.plot(data['wavelength'],data['n'],"-k",label="$n$")
                plt.plot(data['wavelength'],data['k'],"-r",label="$k$")
                plt.xlabel(r"Wavelength ($\mu$m)")
                plt.ylabel(r"Refractive indices $n$,$k$")
                #print(form.ylog.data)
                if form.ylog.data == True:
                    plt.yscale("log")
                plt.xscale("log")
                plt.legend()
                plt.savefig(img, format='svg')
                plt.close()
                img.seek(0)

                plot_urls.append(base64.b64encode(img.getvalue()).decode('utf8'))

            out_l,out_n,out_k = kramers_kronig(data_array)

            #create dictionary object for mixture species
            mixture = {'species' : 'mixture: '+composition_string,
                       'formula' : 'N/A',
                       'wavelength' : out_l,
                       'n' : out_n,
                       'k' : out_k, 
                       'density' : str(density),
                       'temperature' : 'N/A',
                       'stype' : 'N/A',
                       'origin' : 'CALCULATION',
                       'citation' : 'WISCI Distillery' }

            #plot for mixture
            img = io.BytesIO()

            print(species)
            composition_string = ""
            for i in range(0,nspecies):
                composition_string += str(fracs[i])+"x "+species[i]+" "

            x = np.arange(10)
            plt.title("somebodys_plot "+str(datetime.date.today())+" mixture: "+composition_string)
            plt.plot(mixture['wavelength'],mixture['n'],"-k",label="$n$")
            plt.plot(mixture['wavelength'],mixture['k'],"-r",label="$k$")
            plt.xlabel(r"Wavelength ($\mu$m)")
            plt.ylabel(r"Refractive indices $n$,$k$")
            #print(form.ylog.data)
            if form.ylog.data == True:
                plt.yscale("log")
            plt.xscale("log")
            plt.legend()
            plt.savefig(img, format='svg')
            plt.close()
            img.seek(0)
            plot_mixture = base64.b64encode(img.getvalue()).decode('utf8')

            if form.savedata.data == True:
                file_uuid = str(uuid.uuid4())
                filename="distillery_"+file_uuid+".csv"
                np.savetxt("./static/client/"+filename,np.c_[data['wavelength'],data['n'],data['k']])
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

app.run(debug=True)
