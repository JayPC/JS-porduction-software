from datetime import date, timedelta, datetime
import numpy as np
from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response
from flask_fontawesome import FontAwesome
from flask_mysqldb import MySQL
from random import sample, choice
import re
from calendar import monthrange
from passlib.hash import sha256_crypt
import jwt
import string
from functools import wraps

today = date.today()


def getinfoturno():
	dic={}
	p, t = getconfdata()
	mycursor = mysql.connection.cursor()
	res = mycursor.execute("select * from def_turno")
	if res>0:
		myresult = mycursor.fetchall()
		for row in myresult:
			dic['inicio_turno%s' % row[0]] = str(row[1])
			dic['fim_turno%s' % row[0]] = str(row[2])
	return dic

def gethourdata(posto):
	t_pecas = []
	horas = ['08:00:00','09:00:00','10:00:00','11:00:00','12:00:00','13:00:00','14:00:00','15:00:00','16:00:00',
			'17:00:00','18:00:00','19:00:00','20:00:00','21:00:00','22:00:00','23:00:00','00:00:00','01:00:00',
			'02:00:00','03:00:00','04:00:00','05:00:00','06:00:00','07:00:00',]
	mycursor = mysql.connection.cursor()
	for i in horas:
		res = mycursor.execute("Select nr_pecas_periodo, tempo_paragem_total from data%s where hora_inicio_periodo = '%s' and data='%s'" % (posto, i, today))
		if res > 0:
			myresult= mycursor.fetchall()
			for row in myresult:
				pecas = row[0]
		else:
			pecas = 0
		t_pecas.append(int(pecas))
	return t_pecas



def get_data_month(year, cm, posto):
	dt = date(year,cm,1)
	sum_p=0
	for i in range(monthrange(year,cm)[1]):
		d = dt +timedelta(days=i)
		p ,t = get_data_day(posto,d)
		for x in p:
			sum_p +=x
	return sum_p



		

#################################################################NOW############################################################################################
def get_data_day(posto,dia):
	tempo = 0
	total_pecas = []
	total_tempo = []
	mycursor = mysql.connection.cursor()
	for turno in range(1,4):
		res=mycursor.execute("Select total_pecas_bloco, tempo_paragem_total from data%s where id_turno=%s and data='%s'" % (posto, turno, dia))
		if res > 0:
			myresult = mycursor.fetchall()
			for row in myresult:
				pecas = row[0]
				tempo += row[1]
			pass
		else:
			pecas = 0
			tempo = 0
		total_pecas.append(int(pecas))
		total_tempo.append(int(tempo))
	return total_pecas, total_tempo

def prepareDic():
	n_postos, n_turnos = getconfdata()
	a_dic={}
	for x in range (1,n_turnos+1):
		t_str='pecas%s' % x
		a_dic[t_str] = []
		t_str='tempo%s' % x
		a_dic[t_str] = []
	return a_dic


def get_data_week(firstday,posto):
	producao_dic = prepareDic()
	producao_dic['posto'] = posto
	lastday = firstday + timedelta(days=6.9)
	mycursor = mysql.connection.cursor()
	sum_pecas =0
	pecas_posto = []
	while firstday <= lastday:
		pecas, tempo = get_data_day(posto, firstday)
		turno = 1
		for x in pecas:
			sum_pecas += x
			producao_dic['pecas%s' % turno].append(int(x))
			turno+=1
		turno = 1
		for x in tempo:
			producao_dic['tempo%s' % turno].append(int(x))
			turno+=1
		firstday += timedelta(days=1)
	return sum_pecas, producao_dic

##########################################################functions##############################################################################################


def medias_get_data(posto, dias):
	total_pecas_dia = 0
	total_tempo_dia = 0
	total_pecas= []
	tempo=0
	mycursor = mysql.connection.cursor()
	for turno in range(1,4):
		for k in range(dias+1):
			Sel_day= today - timedelta(days=k)
			res = mycursor.execute("Select total_pecas_bloco, tempo_paragem_total, data from data%s where id_turno=%s and data='%s'" % (posto, turno, Sel_day))
			if (res > 0):
				myresult = mycursor.fetchall()
				for row in myresult:
					pecas = row[0]
					tempo += row[1]
			else:
				pecas=0
				tempo=0
			total_pecas_dia += pecas
			total_tempo_dia +=tempo
			tempo = 0
		total_pecas.append(int(total_pecas_dia))
		total_pecas_dia=0
		total_tempo_dia=0
	return total_pecas

def live_data(dia, posto):
	tempo = 0
	total_pecas = []
	total_tempo = []
	mycursor = mysql.connection.cursor()
	Sel_day = today - timedelta(days=dia)
	d = Sel_day.strftime("%d-%m-%Y")
	for turno in range(1,4):
		res=mycursor.execute("Select total_pecas_bloco, tempo_paragem_total from data%s where id_turno=%s and data='%s'" % (posto, turno, Sel_day)) #change date!!!
		if res > 0:
			myresult = mycursor.fetchall()
			for row in myresult:
				pecas = row[0]
				tempo += row[1]
			pass
		else:
			pecas = 0
			tempo = 0
		total_pecas.append(int(pecas))
		total_tempo.append(int(tempo))
	return total_pecas, total_tempo, d

def  getconfdata():
	mycursor = mysql.connection.cursor()
	res= mycursor.execute("Select * from info")
	myresult = mycursor.fetchall()
	for row in myresult:
		p = row[0]
		t = row[1]
	return p , t 

##############################################################FlaskApp#####################################################################################################
def token_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		global token
		#token = request.args.get('token')
		if not token:
			return jsonify({'message': 'Token is missing!'}), 403
		try:
			data = jwt.decode(token, app.config['SECRET_KEY'])
		except:
			return redirect(url_for('login'))
			#return jsonify({'message': 'Token is invalid'}), 403
		return f(*args, **kwargs)
	return decorated

app = Flask(__name__)
fa = FontAwesome(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'andre'
app.config['MYSQL_PASSWORD'] = 'andre199921'
app.config['MYSQL_DB'] = 'indmei'
app.config['SECRET_KEY'] = ''.join(choice(string.ascii_uppercase + string.ascii_lowercase  + string.digits) for _ in range(256))
token = ''

mysql = MySQL(app) 

@app.route('/')
@app.route('/login', methods=['GET' , 'POST'])
def login():
	app.config['MYSQL_DB'] = 'usersLog'
	error = None
	if request.method == 'POST':
		user = request.form['username']
		inserted_password =  request.form['password']
		mycursor = mysql.connection.cursor()
		res = mycursor.execute ("Select password from users where username='%s' " % user)
		if res>0:
			myresult = mycursor.fetchall()
			for row in myresult:
				password = row[0]
			if sha256_crypt.verify(inserted_password, password):
				app.config['MYSQL_DB'] = 'indmei'
				global token
				token = jwt.encode({'user': user, 'exp': datetime.utcnow()+timedelta(minutes=20)},app.config['SECRET_KEY'])
				#return jsonify({'token': token.decode('UTF-8'), 'secret': app.config['SECRET_KEY']})
				#mk_url= 'home?token=%s' % token 
				return redirect(url_for('home'))
			else:
				error = 'Wrong PassWord'
		else:
			error = "Invalid Username"
	return render_template('login.html', error = error)




#		if  request.form['username'] != 'root' or request.form['password'] != 'andre199921':
#			error = 'Invalid credencials. Please try again.'
#		else:
#			return redirect(url_for('home')) 
#	return render_template('login.html', error = error)


@app.route('/home')
def home():
	mycursor = mysql.connection.cursor()
	data = np.zeros((7,7), dtype=int)
	tempo = 0
	for posto in range(1,7):
		for turno in range(1,4):
			#mycursor.execute ("Select total_pecas_bloco, tempo_paragem_total, data from data%s where id_turno=%s and data='%s'" % (posto, turno, today) )
			mycursor.execute ("Select total_pecas_bloco, tempo_paragem_total, data from data%s where id_turno=%s and data='2020-05-03'" % (posto, turno) )
			myresult = mycursor.fetchall()
			for row in myresult:
				pecas = row[0]
				tempo += row[1]	
			data[posto][turno] = pecas
			data[posto][turno+3] = tempo
			tempo = 0
	return render_template('table.html', mydata = data)

@app.route('/data')
def data():
	try:
		data_posto = request.args.get('dowhat')
		data_date = request.args.get('days')
		#p_total = medias_get_data(int(data_posto), int(data_date))
		return jsonify({'results': medias_get_data(int(data_posto), int(data_date))})
	except Exception as e:
		raise e
	return	


@app.route('/live')
def live():
	try:
		dia = int(request.args.get('day'))
		posto = int(request.args.get('posto'))
		new_pecas , new_tempo, day = live_data(dia, posto)
		return jsonify({'same': 0 ,'pecas': new_pecas , 'tempo': new_tempo, 'dia':day })
	
	except Exception as e:
		raise e
	pass

@app.route('/conf')
@token_required
def conf():
	try:
		p, t = getconfdata()
		return render_template('conf.html', postos = p, turnos=t)
	except Exception as e:
		raise e

@app.route('/getconf')
def getconf():
	try:
		p, t = getconfdata()
		return jsonify({'postos': p, 'turnos': t})
	except Exception as e:
		raise e

@app.route('/getconfturno')
def getconfturno():
	data = getinfoturno()
	return jsonify(data)

@app.route('/dashboard')
@token_required
def dashboard():
	return render_template('dashboard.html')

@app.route('/dataweek')
def dataweek():
	w = int(request.args.get('week'))
	currentWeek = today.isocalendar()[1]
	new_week = currentWeek - w
	p_year = 2020
	firstday = datetime.strptime(f'{p_year}-W{int(new_week)- 1}-1', "%Y-W%W-%w").date()
	f = firstday.strftime("%d/%m/%Y")
	pecas = []
	for i in range(1,7):
		p, p_d = get_data_week(firstday,i)
		pecas.append(int(p))
	return jsonify({'results': pecas, 'inicio': f})

@app.route('/selectdata')
def selectdata ():
	dias = int(request.args.get('dias'))
	posto = int(request.args.get('posto'))
	dia = today - timedelta(days=dias)
	pecas = 0
	while dia <= today:
		p,t  = get_data_day( posto, dia)
		for x in p:
			pecas += x
		dia += timedelta(days=1)
	return jsonify({'pecas': pecas, 'posto' : posto})

@app.route('/datamonth')
def datamonth():
	mes = int(request.args.get('mes'))
	posto = int(request.args.get('posto'))
	year = int(request.args.get('year'))
	pec = get_data_month(year, mes, posto)
	return jsonify({'pecas': pec})

@app.route('/livemedias')
@token_required
def livemedias():
	return render_template('daydata.html')

@app.route('/hourdata')
def hourdata():
	posto = int(request.args.get('posto'))
	data = gethourdata(posto)
	t_pecas=0
	cont=0
	for x in data:
		t_pecas+=x
		if(x>0):
			cont+=1
	media = int(t_pecas/cont)
	return jsonify({'pecas': data, 'tot':t_pecas, 'med':media})

@app.route('/producao')
@token_required
def producao():
	return render_template('producao.html')

@app.route('/backproducao')
def backproducao():
	#p, data = get_data_week(first, 2)
	posto = int(request.args.get('posto'))
	currentWeek = today.isocalendar()[1]
	firstday = datetime.strptime(f'2020-W{int(currentWeek)- 1}-1', "%Y-W%W-%w").date()
	f = firstday.strftime("%d/%m/%Y")
	test = firstday - timedelta(days=25)
	p, data = get_data_week(firstday, posto)
	postos, turnos = getconfdata()
	for x in range (1,turnos+1):
		data['pecas%s' % x].append(int(sum(data['pecas%s' % x])))
		data['tempo%s' % x].append(int(sum(data['tempo%s' % x])))
	return jsonify(data)

if __name__== '__main__':
    app.run(debug=True)

################################################################################################################################################################
#mycursor.execute ("Select total_pecas_bloco, tempo_paragem_total, data from data2 where id_turno=3 and data between '2020-04-27' and '2020-04-29'")
