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
#@app.route("/myplot", methods=["GET"])
matplotlib.use('Agg')

class InputForm(Form):
    optcons=glob.glob("./static/opticalconstants/*")
    optcons.sort()
    listopt=[]
    print(optcons)
    for i_optcon,optcon in enumerate(optcons):
        listopt.append((i_optcon,optcon.split("/")[-1].split(".")[0]))
    print(listopt)
    #A = FloatField(label="Amplitude", default=1.0,validators=[validators.NumberRange(min=1,max=10,message="A outside of bounds 1<=A<=10")])
    #b = FloatField(label="Offset", default=1.0,validators=[validators.NumberRange()])
    #n = FloatField(label="Power", default=2.0,validators=[validators.NumberRange(min=1,max=10,message="n outside of bounds 1<=n<=10")])
    
    optc=SelectField("Species",choices=listopt)
    options_sil=SelectMultipleField("Select Silicates (unused)",choices=listopt)
    options_car=SelectMultipleField("Select Carbons (unused)",choices=listopt)
    options_ice=SelectMultipleField("Select Ices (unused)",choices=listopt)
    savedata= BooleanField(label="Make raw data available for download",render_kw={'checked': False})
    ylog= BooleanField(label="Log Y-axis",default="")

app = Flask(__name__)

import datetime

import base64


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



@app.route("/get-data/<path:name>")
def download_file(name):
    return send_from_directory("./static/client/", name, as_attachment=True)

@app.route('/plot',methods=['GET','POST'])
def plot():
    if True:
    #try:
        form=InputForm(request.form)
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
    
app.run(debug=True)
