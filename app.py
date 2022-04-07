from flask import render_template, Flask,send_file,request
from wtforms import Form, FloatField, validators,BooleanField,SelectField
import io
import base64
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import matplotlib.pyplot as plt
#@app.route("/myplot", methods=["GET"])
matplotlib.use('Agg')

class InputForm(Form):
    A = FloatField(label="Amplitude", default=1.0,validators=[validators.NumberRange(min=1,max=10,message="A outside of bounds 1<=A<=10")])
    b = FloatField(label="Offset", default=1.0,validators=[validators.NumberRange()])
    n = FloatField(label="Power", default=2.0,validators=[validators.NumberRange(min=1,max=10,message="n outside of bounds 1<=n<=10")])
    ylog= BooleanField(label="Log Y-axis",default="")
    options=SelectField("Favourite food",choices=[("Pizza","Pizza"),("CAKE","CAKE"),("Pork over rice","Pork over rice"),("Carrot","Carrot")])

app = Flask(__name__)

import datetime

import base64
@app.route('/plot',methods=['GET','POST'])
def plot():
    if True:
    #try:
        form=InputForm(request.form)
        if request.method == 'POST' and form.validate():
            
        
            img = io.BytesIO()
    
            x = np.arange(10)
            plt.title("somebodys_plot "+str(datetime.date.today())+" "+form.options.data)
            plt.plot(x,form.A.data*x**form.n.data+form.b.data)
            print(form.ylog.data)
            if form.ylog.data == True:
                plt.yscale("log")
            plt.savefig(img, format='png')
            plt.close()
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode('utf8')

            return render_template('plot.html', plot_url=plot_url,form=form)
        else:
            plot_url=None
            return render_template('plot.html', plot_url=plot_url,form=form)
    #except:
     #   return render_template('err.html')
    
app.run(debug=True)
