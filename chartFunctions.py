

def loadResults(nameF,
	location='data'):
	import os
	import pickle
	nameF = nameF+'.p'
	inPickPath = os.path.join(location, nameF)
	print("load file: "+inPickPath)
	return pickle.load(open(inPickPath, 'rb'))

#return dataframe/dict/list containing listed fields
def getFields(fields, dictName, year, outType='pandas'):
	import pandas as pd
	import numpy as np
	seriesDict = dict()
	titleKeys = [key for key in dictName[year].keys()]
	for field in fields:
		#print("add "+field+" to "+outType)
		seriesDict[field] = []
		for entry in titleKeys:
			#if statement for title
			if field in ['title']:
				seriesDict[field].append(entry)
			#else if statement for box office fields
			elif field in ['actual','projected','model', 'act','bop','tim','al']:
				boxField = 'boxOffice'
				if field in ['act','bop','tim','al']:
					boxField = 'box'
				if field in dictName[year][entry][boxField].keys():
					if boxField == 'boxOffice':
						seriesDict[field].append(dictName[year][entry][boxField][field][-1])
					else:
						seriesDict[field].append(dictName[year][entry][boxField][field])
				else:
					seriesDict[field].append(float('NaN'))
			#else for rest of the fields
			else:			
				seriesDict[field].append(dictName[year][entry][field])
	if outType=='pandas':
		return pd.DataFrame(seriesDict)
	elif outType=='dict':
		return seriesDict
	elif outType=='list':
		return list(zip(*seriesDict.values()))

#return a dictionary of unique values obs for a given field
def getUniq(field, dictName, year, defval=0):
	dictUniq = dict()
	for key in dictName[year].keys():
		idg = dictName[year][key][field]
		if str(idg) != 'na':
			if idg not in dictUniq.keys():
				#print(str(idg)+" added to unique entry list")
				if defval == 0:
					dictUniq[idg]=defval
				elif defval == 'dict':
					dictUniq[idg]=dict()
				elif defval == 'list':
					dictUniq[idg]=[]
	return dictUniq

#return a dictionary of unique value's summed values
def uniqSum(field, metric, dictName, year):
	sumDict = getUniq(field, dictName, year)
	for entry in dictName[year].keys():
		group = dictName[year][entry][field]
		if group in sumDict.keys():
			if metric in dictName[year][entry]['box'].keys():
				value = dictName[year][entry]['box'][metric] / 1000000
				#print(entry + ": "+str(value)+" added to "+field+" "+str(group))
				sumDict[group] = sumDict[group] + value
	return sumDict

#return a dictionary containing segment specific total spliced values
def getSplice(segment, dictName, year):
	import numpy as np
	spliceDict = getUniq(segment, dictName, year, defval='dict')
	for user in spliceDict.keys():
		spliceDict[user]['observed']=0
		spliceDict[user]['total']=0
	for entry in dictName[year].keys():
		user = dictName[year][entry][segment]
		if user in spliceDict.keys():
			if 'act' in dictName[year][entry]['box'].keys():
				spliceDict[user]['observed'] = spliceDict[user]['observed'] + 1
				actual = dictName[year][entry]['box']['act'] / 1000000
				spliceDict[user]['total']=spliceDict[user]['total'] + actual
			elif 'delayed' in dictName[year][entry].keys():
				spliceDict[user]['total']=spliceDict[user]['total'] + 0
			elif 'bop' in dictName[year][entry]['box'].keys():
				proj = dictName[year][entry]['box']['bop'] / 1000000
				spliceDict[user]['total']=spliceDict[user]['total'] + proj
			else:
				box = np.mean([dictName[year][entry]['box']['al'], 
					dictName[year][entry]['box']['tim']])/1000000
				spliceDict[user]['total']=spliceDict[user]['total'] + box
	return spliceDict

#return a dictionary that contains keys based on unique values of segment and values that are lists
def segVals(segment, metric, dictName, year):
	valDict = getUniq(segment, dictName, year, defval='dict')
	for m in metric:
		for entry in dictName[year].keys():
			group = dictName[year][entry][segment]
			if m not in valDict[group].keys():
				valDict[group][m]=[]
			if m == 'title':
				valDict[group][m].append(entry)
			#else if statement for box office fields
			elif m in ['actual', 'projected', 'model']:
				if m in dictName[year][entry]['boxOffice'].keys():
					valDict[group][m].append(dictName[year][entry]['boxOffice'][m][-1])
				else:
					valDict[group][m].append(float('NaN'))
			#else for rest of the fields
			else:			
				valDict[group][m].append(dictName[year][entry][m])
	return valDict

def heatRankInp(dictName, year):
	from operator import itemgetter
	dataPrelim = dict()
	dataPick = dict()
	inpComb = []
	for title in dictName[year].keys():
		if 'actual' in dictName[year][title]['boxOffice'].keys():
			box = dictName[year][title]['boxOffice']['actual'][-1]
		else:
			box = 0
		dataPrelim[title]=box
		dataPick[title]=dictName[year][title]['overallPick']
	r = {key: rank for rank, key in enumerate(sorted(set(dataPrelim.values()), 
		reverse=True), 1)}
	t = {k: r[v] for k,v in dataPrelim.items()}
	for entry,pick in dataPick.items():
		rank = t[entry]
		pickL = str(pick)
		inpComb.append([entry,pick,rank,pickL,' '])
	inpSorted = sorted(inpComb, key=itemgetter(1))
	return zip(*inpSorted)

#return a dictionary that contains a list of titles within a segment
def getPicks(segment, dictName, year):
	groupDict = getUniq(segment, dictName, year, defval='list')
	for entry in dictName[year].keys():
		group = dictName[year][entry][segment]
		if group != 'na':
			groupDict[group].append(entry)
	return groupDict

#return user specific cumulative time series
def userCume(dictName, year, segment='id', month=1, day=1):
	import datetime
	import numpy as np
	cumeDict = getUniq(segment, dictName, year, defval='dict')
	titleDict = getPicks(segment, dictName, year)
	schedDict = dict()
	for entry in dictName[year]:
		rd = dictName[year][entry]['releaseDate']
		rdF = datetime.datetime.strptime(rd, '%d-%b-%y').date()
		schedDict[entry] = rdF
	start = datetime.date(year, month, day)
	end = datetime.date(year+1, 1, 1)
	for pid in cumeDict:
		grossCume = 0
		for n in range(int ((end - start).days)):
			label = ''
			day = (start + datetime.timedelta(n))
			if len(titleDict[pid])>0:
				for title in titleDict[pid]:
					if schedDict[title] == day:
						if 'act' in dictName[year][title]['box'].keys():
							box = dictName[year][title]['box']['act']/1000000
							label = title+': '+str(box)+' (actual)'
						elif 'delayed' in dictName[year][title].keys():
							box = 0
							label = title+': Delayed'
						elif 'bop' in dictName[year][title]['box'].keys():
							box = dictName[year][title]['box']['bop']/1000000
							label = title+': '+str(box)+' (BOP proj.)'
						else:
							box = np.mean([dictName[year][title]['box']['al'], 
								dictName[year][title]['box']['tim']])/1000000
							label = title+': '+str(box)+' (Expert proj.)'
						grossCume = grossCume + box
						#titleDict[pid].remove(title)
			cumeDict[pid][day] = [grossCume,label]

	return cumeDict
