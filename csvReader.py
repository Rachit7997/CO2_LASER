import os
import csv

error = None

class CSVReader():
	def __init__(self,loc=""):
		if loc=="":
			self.path=""
		else:
			if (self.setPath(loc)):
			    pass
			else:
				print("Warning: Path Don't Exists..!")
				self.path=""
	
	def setPath(self,x):
		global error
		try:
			if type(x)==str:
				if os.path.exists(x):
					self.path=x
					return(True)
				else:
					x=makeCSV(x)
					if x != False:
						self.path=x
					return(True)
			else:
				return (False)
		except Exception as e:
			#print(e)
			error = "setPath: " + str(e)
			return (False)
			
	def getDuties(self,frq):
		global error
		try:
			f=open(self.path,'r')
			x=csv.DictReader(f)
			duty=[]
			for r in x:
				if str(r["F"])==str(frq):
					duty.append(int(r["D1"]))
					duty.append(int(r["D2"]))
					duty.append(int(r["D3"]))
					duty.append(int(r["D4"]))
					duty.append(int(r["D5"]))
					duty.append(int(r["D6"]))
					duty.append(int(r["D7"]))
					duty.append(int(r["D8"]))
			return(duty)
		except Exception as e:
			#print(e)
			error = "getDuties: "+ str(e)
			return list()
			
	def getData(self,frq):
		global error
		try:
			f=open(self.path,'r')
			x=csv.DictReader(f)
			duty=[]
			power=[]
			for r in x:
				if str(r["F"])==str(frq):
					duty.append(int(r["D0"]))
					duty.append(int(r["D1"]))
					duty.append(int(r["D2"]))
					duty.append(int(r["D3"]))
					duty.append(int(r["D4"]))
					duty.append(int(r["D5"]))
					duty.append(int(r["D6"]))
					duty.append(int(r["D7"]))
					duty.append(int(r["D8"]))
					power.append(float(r["P0"]))
					power.append(float(r["P1"]))
					power.append(float(r["P2"]))
					power.append(float(r["P3"]))
					power.append(float(r["P4"]))
					power.append(float(r["P5"]))
					power.append(float(r["P6"]))
					power.append(float(r["P7"]))
					power.append(float(r["P8"]))
			error = "Here is your error!"
			return(duty , power)
		except Exception as e:
			print(e)
			error = "getData: " + str(e)
			return(list(),list())
			
	def setPower(self,freq,Power,Duty):
		global error
		if type(Power)==list and type(Duty) == list and len(Power)==len(Duty)==8:
			try:
				fout=self.path.replace('.csv','_temp.csv')
				fileIn=open(self.path,'r')
				fileOut=open(fout,'w')
				cvsIN=csv.DictReader(fileIn)
				fileOut.write("F,P1,D1,P2,D2,P3,D3,P4,D4,P5,D5,P6,D6,P7,D7,P8,D8\n")
				for r in cvsIN:
					if str(r["F"])== str(freq):
						row=str(freq)+","+str(Power[0])+","+str(Duty[0])
						row=row+","+str(Power[1])+","+str(Duty[1])
						row=row+","+str(Power[2])+","+str(Duty[2])
						row=row+","+str(Power[3])+","+str(Duty[3])
						row=row+","+str(Power[4])+","+str(Duty[4])
						row=row+","+str(Power[5])+","+str(Duty[5])
						row=row+","+str(Power[6])+","+str(Duty[6])
						row=row+","+str(Power[7])+","+str(Duty[7])
						row=row+"\n"
						fileOut.write(row)
					else:
						row=str(r["F"])+","+str(r["P1"])+","+str(r["D1"])
						row=row+","+str(r["P2"])+","+str(r["D2"])
						row=row+","+str(r["P3"])+","+str(r["D3"])
						row=row+","+str(r["P4"])+","+str(r["D4"])
						row=row+","+str(r["P5"])+","+str(r["D5"])
						row=row+","+str(r["P6"])+","+str(r["D6"])
						row=row+","+str(r["P7"])+","+str(r["D7"])
						row=row+","+str(r["P8"])+","+str(r["D8"])+"\n"
						fileOut.write(row)		
				fileOut.close()
				fileIn.close()
				fileIn=open(fout,'r')
				fileOut=open(self.path,'w')
				for x in fileIn.readlines():
					fileOut.write(x)
				fileOut.close()
				fileIn.close()
				os.remove(fout)
				return(True)
			except Exception as e:
				error = "setPower: " + str(e)
				#print(e)
				return(False)
		else:
			return(False)

			
def makeCSV(path):
	global error
	try:
		if type(path)==str :
			if  not ".csv" in path:
				path=path+".csv"
				f=open (path,'w')
			else:
				f=open(path,'w')
			f.write("F,P1,D1,P2,D2,P3,D3,P4,D4,P5,D5,P6,D6,P7,D7,P8,D8\n");
			f.write("1,,10,,14,,28,,42,,56,,70,,84,,90\n");
			f.write("2,,10,,15,,28,,42,,55,,69,,82,,90\n");
			f.write("3,,10,,16,,29,,42,,55,,68,,81,,90\n");
			f.write("4,,10,,16,,29,,41,,54,,66,,79,,90\n");
			f.write("5,,10,,17,,29,,41,,53,,65,,77,,90\n");
			f.write("6,,10,,17,,29,,41,,52,,64,,76,,88\n");
			f.write("7,,10,,18,,29,,40,,52,,63,,74,,86\n");
			f.write("8,,10,,18,,29,,40,,51,,62,,73,,84\n");
			f.write("9,,10,,19,,29,,40,,50,,61,,71,,82\n");
			f.write("10,,10,,20,,30,,40,,50,,60,,70,,80\n");
			f.write("11,,10,,19,,29,,39,,49,,59,,69,,79\n");
			f.write("12,,11,,20,,29,,39,,48,,58,,67,,77\n");
			f.write("13,,12,,21,,30,,39,,48,,57,,66,,75\n");
			f.write("14,,13,,21,,30,,38,,47,,55,,64,,73\n");
			f.write("15,,14,,22,,30,,38,,46,,54,,62,,71\n");
			f.write("16,,15,,22,,30,,38,,45,,53,,61,,69\n");
			f.write("17,,16,,23,,30,,37,,45,,52,,59,,67\n");
			f.write("18,,17,,23,,30,,37,,44,,51,,58,,65\n");
			f.write("19,,18,,24,,30,,37,,43,,50,,56,,63\n");
			f.write("20,,19,,25,,31,,37,,43,,49,,55,,61\n");
			f.write("21,,19,,24,,30,,36,,42,,48,,54,,60\n");
			f.write("22,,20,,25,,30,,36,,41,,47,,52,,58\n");
			f.write("23,,21,,26,,31,,36,,41,,46,,51,,56\n");
			f.write("24,,22,,26,,31,,35,,40,,44,,49,,54\n");
			f.write("25,,23,,27,,31,,35,,39,,43,,47,,52\n");
			f.close()
			return (path)
	except Exception as e:
		#print (e)
		error = "makeCSV" + str(e)
		return (False)
