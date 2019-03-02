
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
# import draftFunctions as dF
# import head2Head.head2Head as h2h
import plotly.graph_objs as go
import plotly.figure_factory as ff
import numpy as np
import datetime
import chartFunctions as cF

draft = cF.loadResults(nameF='BoxOfficeDraft')
boxDict = cF.loadResults(nameF='Head2Head')
yearVals = list(draft.keys())


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions']=True
application = app.server
app.title = 'Movie Draft Tracking and Results'
app.layout = html.Div([
	html.H1('Movie Draft Tracking and Results'),
	dcc.Tabs(id='draftTabs', value='singleYr', children=[
		dcc.Tab(label='Single Year Analysis', value='singleYr'),
		dcc.Tab(label='Multiple Year Analysis', value='multiYr')
	]),
	html.Div(id='draftTabsContent')
])

@app.callback(Output('draftTabsContent', 'children'),
	[Input('draftTabs', 'value')])
def render_content(tab):
	if tab == 'singleYr':
		return html.Div([
			html.Div([
				html.H2('Single Year Analysis'),
				html.Label('Choose Draft Year: '),
				dcc.Dropdown(
					id='year-dropdown',
					options=[{'label': str(year), 'value': str(year)} for year in yearVals],
					value=str(max(yearVals))
			    )
			]),
			html.Div([
				html.Div([
					html.H3('Summary Table'),
					dcc.Graph(id='aggTable', style={'height':400})
				], className='six columns'),
				html.Div([
					html.H3('Stacked Actuals'),
					dcc.Graph(id='graph-with-slider2', style={'height':400, 'border': '1px solid #333'})	
				], className='six columns')
			], className='row'),

			html.Div([
				html.H3('Cumulative Spliced'),
				dcc.Graph(id='graph-with-slider1', style={'height':400, 'border': '1px solid #333'})
			])
		])
	elif tab == 'multiYr':
		return html.Div([
			html.Div([
				html.H2('Multiple Year Analysis'),
				html.Label('Choose Draft Year(s): '),
				dcc.Dropdown(
					id='year-multichoice',
					options=[{'label': str(year), 'value': str(year)} for year in yearVals],
					value=[max(yearVals)],
					multi=True
				)
			]),

			html.Div([
				html.Div([
					html.H3('Space Holder')
				], className='six columns'),
				html.Div([
					html.H3('Round Pick Distribution'),
					dcc.Graph(id='boxWhisk', style={'height':400})
				], className='six columns')
			], className='row')
		])

@app.callback(
	dash.dependencies.Output('graph-with-slider1', 'figure'),
	[dash.dependencies.Input('year-dropdown', 'value')])
def update_figure_1(selected_year):
	yr = int(selected_year)
	cumeInput = cF.userCume(boxDict,yr)
	cumeCharts = dict()
	cumeData = []
	for i in cumeInput.keys():
		cumeCharts[i] = sorted(np.array(cumeInput[i].items()).tolist())
		xData,yDataLabel = zip(*cumeCharts[i])
		yData,cumeLabel = zip(*yDataLabel)
		fig = go.Scatter(x=xData,
				y=yData,
				mode='lines+markers',
				marker=dict(size='2'),
				text=cumeLabel,
				name=i)
		cumeData.append(fig)
	now = datetime.datetime.now()
	if now.year == yr:
		#asof = 'as of '+now.strftime('%b-%d-%Y')
		vLine= [
		# Line Vertical
			{'type': 'line',
			'x0': now,
			'y0': 0,
			'x1': now,
			'y1': 600,
			'line': {
			'color': 'black',
			'width': 3,
			},
		}]
	else:
		asof = str(selected_year)
		vLine=list()
	cumeLayout= go.Layout(legend=dict(x=0, y=1),
		shapes= vLine,
		margin={'t':25, 'b':20})
	return {
		'data': cumeData, 
		'layout': cumeLayout
	}

@app.callback(
	dash.dependencies.Output('graph-with-slider2', 'figure'),
	[dash.dependencies.Input('year-dropdown', 'value')])
def update_figure_2(selected_year):
	yr = int(selected_year)
	roundDict = cF.segVals('round',['title','actual','id'],draft,yr)
	stack = []
	for i in roundDict.keys():
	    stackInp = go.Bar(x=roundDict[i]['id'], 
	        y=roundDict[i]['actual'], 
	        text=roundDict[i]['title'], 
	        name=str(i))
	    stack.append(stackInp)
	stackLayout = go.Layout(barmode='stack',
		margin={'t':10, 'b':15, 'l':35})
	stackFig = go.Figure(data=stack, layout=stackLayout)
	return {
		'data': stack, 
		'layout': stackLayout
	}

@app.callback(
	dash.dependencies.Output('boxWhisk', 'figure'),
	[dash.dependencies.Input('year-multichoice', 'value')])
def update_box_whisk(selectedYrs):
	if selectedYrs == None:
		return
	draftDict = dict()
	for i in selectedYrs:
		draftDict[i] = cF.segVals('round',['actual'],draft,int(i))
	boxWhisk = []
	combDict = dict()
	for i in draftDict.keys():
		for z in draftDict[i].keys():
			if z in combDict.keys():
				combDict[z] = combDict[z]+draftDict[i][z]['actual']
			else:
				combDict[z] = draftDict[i][z]['actual']

	for i in combDict.keys():
	    tempInp = go.Box(y=combDict[i], 
	        name='Round '+str(i), 
	        boxpoints = 'all',
	        marker=dict(size=5), 
	        line=dict(width=2))
	    boxWhisk.append(tempInp) 
	boxWhiskLayout = go.Layout(showlegend=False,
		margin={'t':10, 'b':25, 'l':35})
	#boxWhiskFig = go.Figure(data=boxWhisk, layout=boxWhiskLayout)
	return {
		'data': boxWhisk,
		'layout': boxWhiskLayout
	}

@app.callback(
	dash.dependencies.Output('aggTable', 'figure'),
	[dash.dependencies.Input('year-dropdown', 'value')])
def get_agg_table(selected_year):
	yr = int(selected_year)
	#get aggregate values of actual and projected
	aggIdAct = cF.uniqSum('id', 'act', boxDict, yr)
	#get number observed/spliced values (actual where obs/projected otherwise)
	splicedInfo = cF.getSplice('id',boxDict,yr)
	actPanda = pd.DataFrame(aggIdAct, index = ['Actual'])
	splPanda = pd.DataFrame(splicedInfo)
	tableApp = actPanda.append(splPanda)
	tableInp = tableApp.T
	tableInp = tableInp.round({'Actual':2, 'total':2})
	tableInp['observed'] = tableInp['observed'].astype(int)
	tableInp.reset_index(level=0, inplace=True)
	tableInp.sort_values(by='Actual', inplace=True, ascending=False)
	idDict = {'index' : 'Participant', 
	    'Actual' : 'Actual, Mil.$', 
	    'total' : 'Spliced, Mil.$',
	    'observed' : 'Picks Observed'}
	tableInp.columns=[idDict.get(x, x) for x in tableInp.columns]
	rows = tableInp.shape[0]+1
	hCon = 375.0/rows
	fullTable = ff.create_table(tableInp, height_constant=hCon)
	return fullTable


if __name__ == '__main__':
	application.run_server(debug=True)
