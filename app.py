#https://community.plot.ly/t/two-graphs-side-by-side/5312/2
#https://community.plot.ly/t/dash-datatable-using-callbacks/6756
#https://github.com/plotly/dash-table-experiments/blob/master/usage-callback.py
#https://community.plot.ly/t/row-update-in-dash-table-datatable/15564/3
import dash
import dash_core_components as dcc
import dash_html_components as html
# import dash_table_experiments as dt
import dash_table as dt
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
aggTabCols = [{'name':'Player', 'id':'Player'},
	    {'name':'Actual', 'id':'Actual'},
	    {'name':'Spliced', 'id':'Spliced'},
	    {'name':'Picks Obs.', 'id':'Picks Obs.'}]
schedTabCols = [{'name': 'Date','id': 'Date'},
	{'name':'Title', 'id':'Title'},
	{'name': 'Act.','id': 'Act.'},
	{'name': 'Proj.','id': 'Proj.'},
	{'name': 'Player','id': 'Player'},
	{'name': 'Pick','id': 'Pick'}
]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions']=True
#application = app.server
app.title = 'Movie Draft Tracking and Results'
app.layout = html.Div([
	html.H1('Movie Draft Tracking and Results', style={'text-align':'center'}),
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
				#html.H2('Single Year Analysis'),
				html.Label('Choose Draft Year: '),
				dcc.Dropdown(
					id='year-dropdown',
					options=[{'label': str(year), 'value': str(year)} for year in yearVals],
					value=str(max(yearVals)),
					style={'width': 300}
			    )
			]),
			html.Div([
				html.Div([html.H5('Aggregate Results'),
				dt.DataTable(id='aggTable', 
					columns=aggTabCols, 
					data='aggTabRows',
					style_table={
				        'height': '180px',
				        'overflowY': 'scroll',
				        'border': 'thin lightgrey solid'
				    },
				    style_cell={
				    	'textAlign':'center',
				    	'width': '150px'
				    },
				    style_cell_conditional=[
				        {
				            'if': {'column_id': 'Player'},
				            'textAlign': 'left',
				            'width': '150px'
				        }
				    ]+[
				        {
				            'if': {'row_index': 'odd'},
				            'backgroundColor': 'rgb(248, 248, 248)'
				        }
				    ],
				    style_header={
				        'fontWeight': 'bold'
				    },
				    sorting=True,
        			sorting_type="multi",
        			# n_fixed_rows=1
			    ),
			    html.H5('Release Schedule'),
			    dt.DataTable(id='schedTable', 
					columns=schedTabCols, 
					data='schedTable',
					style_table={
				        'height': '180px',
				        'overflowY': 'scroll',
				        'border': 'thin lightgrey solid'
				    },
				    style_cell={
				    	'textAlign':'center',
				    	'textOverflow': 'ellipsis'
				    },
				    style_cell_conditional=[
				        {
				            'if': {'column_id': c},
				            'textAlign': 'left',
				            'whiteSpace': 'no-wrap',
				            'overflow': 'hidden',
				            'maxWidth': '0px',
				            'maxWidth': '125px',
				            'textOverflow': 'ellipsis'
				        } for c in ['Player', 'Title']
				    ]+[
				        {
				            'if': {'row_index': 'odd'},
				            'backgroundColor': 'rgb(248, 248, 248)'
				        }
				    ],
				    style_header={
				        'fontWeight': 'bold'
				    },
				    sorting=True,
        			sorting_type="multi",
				)
				],className='six columns'),
				html.Div([
					html.H5('Stacked Actuals'),
					dcc.Graph(id='graph-with-slider2', style={'height':400, 'border': '2px solid #D3D3D3'})	
				], className='six columns')
			], className='row'),

			html.Div([
				html.H5('Cumulative Spliced'),
				dcc.Graph(id='graph-with-slider1', style={'height':375, 'border': '2px solid #D3D3D3'})
			])
		])
	elif tab == 'multiYr':
		return html.Div([
			html.Div([
				#html.H2('Multiple Year Analysis'),
				html.Label('Choose Draft Year(s): '),
				dcc.Dropdown(
					id='year-multichoice',
					options=[{'label': str(year), 'value': str(year)} for year in yearVals],
					value=[max(yearVals)],
					multi=True,
					style={'width': 300}
				)
			]),

			html.Div([
				html.Div([
					html.H5('Overall Pick Distribution'),
					dcc.Graph(id='scatterPick', style={'height':375, 'border': '2px solid #D3D3D3'})
				], className='six columns'),
				html.Div([
					html.H5('Round Pick Distribution'),
					dcc.Graph(id='boxWhisk', style={'height':375, 'border': '2px solid #D3D3D3'})
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
		margin={'t':25, 'b':20, 'r': 5, 'l': 30})
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
	        name='RD '+str(i), 
	        boxpoints = 'all',
	        marker=dict(size=5), 
	        line=dict(width=2))
	    boxWhisk.append(tempInp) 
	boxWhiskLayout = go.Layout(showlegend=False,
		margin={'t':10, 'b':25, 'l':35, 'r':20})
	#boxWhiskFig = go.Figure(data=boxWhisk, layout=boxWhiskLayout)
	return {
		'data': boxWhisk,
		'layout': boxWhiskLayout
	}

@app.callback(
	dash.dependencies.Output('aggTable', 'data'),
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
	idDict = {'index' : 'Player', 
	    'Actual' : 'Actual', 
	    'total' : 'Spliced',
	    'observed' : 'Picks Obs.'}
	tableInp.columns=[idDict.get(x, x) for x in tableInp.columns]
	return tableInp.to_dict("rows")

@app.callback(
	dash.dependencies.Output('schedTable', 'data'),
	[dash.dependencies.Input('year-dropdown', 'value')])
def get_sched_table(selected_year):
	yr = int(selected_year)
	pdSched = cF.getFields(['releaseDate','title','act','bop','al','tim','id','overallPick'],boxDict,yr)
	pdSched['expert']=pdSched[['tim','al']].mean(axis=1)
	pdSched['Proj.']=pdSched['bop']
	pdSched.loc[np.isnan(pdSched['Proj.']), 'Proj.']=pdSched['expert']
	pdSched['Pick']=pd.to_numeric(pdSched['overallPick'], errors='coerce')
	trimmed=pdSched.dropna(subset=['Pick'])
	trimmed['Date']=pd.to_datetime(trimmed['releaseDate'])
	sched = trimmed[['Date','title', 'act','Proj.','id','Pick']]
	nameDict = {
	 	'act': 'Act.',
	 	'title':'Title',
	 	'id': 'Player',
	}
	sched.rename(index=str, columns=nameDict, inplace=True)
	sched['Act.']=sched['Act.']/1000000
	sched = sched.round({'Act.':2})
	sched['Proj.']=sched['Proj.']/1000000
	return sched.to_dict("rows")

@app.callback(
	dash.dependencies.Output('scatterPick', 'figure'),
	[dash.dependencies.Input('year-multichoice', 'value')])
def scatter_plot(selectedYrs):
	if selectedYrs == None:
		return
	scatterDict = dict()
	for i in selectedYrs:
		scatterData = cF.getFields(['overallPick','actual','title'],
		    draft,int(i))
		#sort dataframe by overall pick
		scatterData = scatterData.sort_values(by=['overallPick'])
		#scatter actual vs projections vs fitted over overall pick
		scatterDict[i] = go.Scatter(x=scatterData['overallPick'], 
		    y=scatterData['actual'],
		    mode='markers',
		    marker=dict(size='10',
		        opacity=0.5),
		    name=i,
		    text= scatterData['title'])
	scatterList = list(scatterDict.values())
	scatterLayout= go.Layout(
	    xaxis= dict(
	        #title= 'Overall Pick',
	        ticklen= 5,
	        zeroline= False,
	        gridwidth= 2),
	    margin={'t':10, 'b':35, 'l':35, 'r':20})
	return {
		'data': scatterList,
		'layout': scatterLayout
	}

if __name__ == '__main__':
	#application.run_server(debug=True)
	app.run_server(debug=True)
