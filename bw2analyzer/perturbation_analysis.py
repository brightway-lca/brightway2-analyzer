# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 17:34:13 2022

@author: SarahSchmidt
"""

import matplotlib.pyplot as plt 
import numpy as np
import pandas as pd
import brightway2 as bw
import presamples
import time
import plotly.express as px

def select_parameters_by_activity_list(activity_list,exc_type='all'):
    '''arguments:
       activity_list: list of activities to be considered
       exc_type: "technosphere", "biosphere" or "all" (default: all)
       
       returns:
       list of all exchanges of the activities included in the activity list
       matching the given exchange type'''
    exchange_list=[]
    for activity in activity_list:
        if exc_type == 'all':
            for exchange in activity.technosphere():
                exchange_list.append(exchange)
            for exchange in activity.biosphere():
                exchange_list.append(exchange) 
        elif exc_type == 'technosphere':
            for exchange in activity.technosphere():
                exchange_list.append(exchange)
        elif exc_type == 'biosphere':
            for exchange in activity.biosphere():
                exchange_list.append(exchange)  
        else:
            print('Error: exc_type has to be "technosphere", "biosphere" or "all"')
    
    return exchange_list


def select_parameters_by_supply_chain_level(
    activity,
    level=0,
    max_level=1,
    first=True,
    exchange_list=None):
    '''arguments:  
         activity_list: activity
         max_level: maximum level of supply chain to be analyzed
       
         returns:
         list of all exchanges of the activities that are part
         of the selected section of the supply chain'''
    
    if first == True:
        exchange_list=[]
     
    if level < max_level: 
        for exc in activity.exchanges():
            if exc['type']!='production':
                exchange_list.append(exc)
            if exc['type']=='technosphere':
                select_parameters_by_supply_chain_level(
                    activity=exc.input,
                    level=level+1,
                    max_level=max_level,
                    first=False,
                    exchange_list=exchange_list)
    return exchange_list

def check_for_duplicates(param_list):
    '''
    arguments:
        param_list : list with bw.exchanges
    returns: prints duplicated items

    '''
    input_output_list=[]
    for exc in param_list:
        input_output_list.append((exc.input['code'],exc.output['code']))
    for elem in input_output_list:
        if input_output_list.count(elem) > 1:
            print(elem)
    return

def check_for_loops(param_list, remove=True):
    '''
    arguments:
        param_list : list with bw.exchanges
        remove: boolean, if remove is True, loop-exchanges are removed from the parameter list
    returns: param_list
    output: prints loop exchanges

    '''
    loops=[]
    for e,exc in enumerate(param_list):
        if exc.input['code']==exc.output['code']:
            loops.append(e)
            print(exc)
            
    if remove==True:
        loops.reverse()
        for e in loops:
            param_list.pop(e)
        
    return param_list


    
def check_for_zeros(param_list, remove=True):
    '''
    arguments:
        param_list : list with bw.exchanges
        remove: boolean, if remove is True, loop-exchanges are removed from the parameter list
    returns: param_list
    output: prints exchanges with amount = 0

    '''
    zeros=[]
    for e,exc in enumerate(param_list):
        if exc.amount == 0:
            zeros.append(e)
            print(exc)
            
    if remove==True:
        zeros.reverse()
        for e in zeros:
            param_list.pop(e)
            
        return param_list



def parameters_to_dataframe(parameter_list,category_type=None,
                            category_dict=None):
    '''arguments:  
        parameter_list: list of exchanges to be considered
        category_type: None, "activity", "input", "location" or "type" 
                      (default: None)
        category_dict: A dictionary assigning categories (values) to keywords (keys). 
                      Needs to be defined in case *category_type* is "activity",
                      "input" or "location". (default: None)
       
        returns:list of all exchanges of the activities included in the
                activity list matching the given exchange type'''
    perturb_input=pd.DataFrame()
       
    for e,exc in enumerate(parameter_list):
        perturb_input.loc[e,'from']=exc.input['name']
        perturb_input.loc[e,'from - code']=exc.input['code']
        if exc['type']=='technosphere':
            perturb_input.loc[e,'from - location']=exc.input['location']
        else:
            perturb_input.loc[e,'from - location']=str(exc.input['categories'])
        perturb_input.loc[e,'to']=exc.output['name']
        perturb_input.loc[e,'to - code']=exc.output['code']
        perturb_input.loc[e,'type']=exc['type']  
        perturb_input.loc[e,'category']=None
        perturb_input.loc[e,'default amount']=exc['amount']

    for i in perturb_input.index:
        perturb_input['run'+str(i)]=perturb_input['default amount']
        perturb_input.loc[i, 'run'+str(i)]=perturb_input.loc[i,'default amount']*1.01
        
    if category_type == None:
        perturb_input['category']=['parameter' for i in range(len(perturb_input.index))]
    elif category_type == "activity":
        for i in perturb_input.index:
            for key in category_dict.keys():
                if key in perturb_input.loc[i,'to']:
                    perturb_input.loc[i,'category']=category_dict[key]
            if perturb_input.loc[i,'category']==None:
                perturb_input.loc[i,'category']='others'
    elif category_type == "input":
        for i in perturb_input.index:
            for key in category_dict.keys():
                if key in perturb_input.loc[i,'from']:
                    perturb_input.loc[i,'category']=category_dict[key]
            if perturb_input.loc[i,'category']==None:
                perturb_input.loc[i,'category']='others'
    elif category_type == "location":
        for i in perturb_input.index:
            for key in category_dict.keys():
                if key == perturb_input.loc[i,'from - location']:
                    perturb_input.loc[i,'category']=category_dict[key]    
            if perturb_input.loc[i,'category']==None:
                perturb_input.loc[i,'category']='others'
    elif category_type == "type":
        perturb_input['category']=perturb_input['type']
    else:
        print('Error: Wrong category type. Allowed category types: None, "location", "activity", "input".')
    perturb_input['category']=perturb_input['category'].replace(np.nan,'others')
    
    return perturb_input



def create_presamples(perturb_input,database_name):
    '''
        arguments:
           perturb_input: dataframe containing input data for the perturbation analysis (output of the function parameters_to_dataframe)
           database_name: name of the database used
       
        returns:
           results of the reproduced LCA calculations for an incremental increase of each parameter individually (columns: methods, indices: runs of the LCA calculation ("default" refers to the default LCA results, "run-i" refers to the reproduced calculation for an incremental increase of parameter i --> cf. index in perturb_input)

    '''
    
    parametersets_matrix_data=[]
    for i in perturb_input.index:
        if perturb_input.loc[i,'type']!='biosphere':
            dataset=(np.array([x for x in perturb_input.loc[i][7:]]).reshape(1,len(perturb_input.columns[7:])),
                     [((database_name, perturb_input.loc[i, 'from - code']),
                      (database_name, perturb_input.loc[i, 'to - code']),
                     'technosphere')],
                    'technosphere')
        else:
            dataset=(np.array([x for x in perturb_input.loc[i][7:]]).reshape(1,len(perturb_input.columns[7:])),
                     [(('biosphere3', perturb_input.loc[i, 'from - code']),
                      (database_name, perturb_input.loc[i, 'to - code']))],
                    'biosphere')
        parametersets_matrix_data.append(dataset)
        
    parameter_id, parameter_path = presamples.create_presamples_package(
                            matrix_data = parametersets_matrix_data,
                            seed='sequential')
    return parameter_path


def perform_perturbation_analysis(functional_unit,LCIA_methods,
                                  perturb_input,
                                  database_name):
    '''
    arguments:  
        functional unit: {activity : amount}
        LCIA methods: list containing at least one bw.methods-item
        perturb_input: dataframe containing input data for the perturbation analysis (output of the function *parameters_to_dataframe*)
        database_name: name of the database used
       
    returns:
        results of the reproduced LCA calculations for an incremental increase of each parameter individually (columns: methods, indices: runs of the LCA calculation ("default" refers to the default LCA results, "run-i" refers to the reproduced calculation for an incremental increase of parameter i --> cf. index in *perturb_input*)

    The caluclation is performed using *presamples*. (cf. https://presamples.readthedocs.io/en/latest/use_with_bw2.html, Lesage et al. 2018: https://doi.org/10.1007/s11367-018-1444-x)

    '''
    parameter_path=create_presamples(perturb_input,database_name)
    
    C_matrices={}
    non_stochastic_lca=bw.LCA(functional_unit)
    non_stochastic_lca.lci()
    for method in LCIA_methods:
        non_stochastic_lca.switch_method(method)
        C_matrices[method] = non_stochastic_lca.characterization_matrix

    start_time=time.time()
    score=[]


    perturb_results={}
    lca=bw.LCA(functional_unit, LCIA_methods[0], presamples=[parameter_path])
    lca.lci()
    lca.lcia()
    score.append(lca.score)

    for ps in range(len(perturb_input.columns[7:])):
        presamp=perturb_input.columns[7:][ps]
        if ps==0:
            inventory=lca.inventory
        else:
            lca.presamples.update_matrices()
            lca.redo_lci()
            inventory=lca.inventory

        results_ps={}        

        for n,IC in enumerate(C_matrices.keys()):
            results_ps[str(IC)]=(C_matrices[IC]*inventory).sum()

        perturb_results[presamp]=results_ps

    perturb_results=pd.DataFrame.from_dict(perturb_results, orient='index')
    perturb_results=perturb_results.rename(index={'default amount':'default'})
    print("--- %s seconds ---" % round((time.time() - start_time),2))
    return perturb_results



def calculate_sensitivity_ratios(LCIA_methods,perturb_results, perturb_input):
    
    '''
    arguments:  
        LCIA methods: list containing at least on bw.methods-item
        perturb_input: dataframe containing input data for the perturbation analysis
        (output of the function *parameters_to_dataframe*)
        perturb_results: output of *perform_perturbation_analysis*
       
    returns:
        DataFrame containing sensitivity ratios per parameter and impact category
    '''    
    
    
    delta_results_relative={}

    for IC in LCIA_methods:
        delta_results_relative_IC={}
        for i in perturb_results.index[1:]:
            delta_results_relative_IC[i]=(perturb_results.loc[i,str(IC)]-perturb_results.loc['default',str(IC)])/perturb_results.loc['default',str(IC)]
        delta_results_relative[str(IC)]=delta_results_relative_IC    
    delta_results_relative

    delta_parameter_relative={}
    for i in perturb_input.index:
        delta_parameter_relative[i]=(perturb_input.loc[i,'run'+str(i)]-perturb_input.loc[i,'default amount'])/perturb_input.loc[i,'default amount']
    delta_parameter_relative

    sensitivity_ratio={}
    for IC in LCIA_methods:
        sensitivity_ratio_IC={}
        for i in perturb_input.index:
            sensitivity_ratio_IC[i]=delta_results_relative[str(IC)]['run'+str(i)]/delta_parameter_relative[i]
        sensitivity_ratio[str(IC)]=sensitivity_ratio_IC
    sensitivity_ratio

    sensitivity_ratio_df=pd.DataFrame()
    sensitivity_ratio_df['from']=perturb_input['from']
    sensitivity_ratio_df['from - code']=perturb_input['from - code']
    sensitivity_ratio_df['from - location']=perturb_input['from - location']
    sensitivity_ratio_df['to']=perturb_input['to']
    sensitivity_ratio_df['to - code']=perturb_input['to - code']
    sensitivity_ratio_df['type']=perturb_input['type']
    sensitivity_ratio_df['category']=perturb_input['category']

    for i in sensitivity_ratio_df.index:
        for IC in LCIA_methods:
            sensitivity_ratio_df.loc[i,str(IC)]=sensitivity_ratio[str(IC)][i]
    return sensitivity_ratio_df


def calculate_sensitivity_coefficients(LCIA_methods, perturb_results, perturb_input):
    '''
    arguments:  
        LCIA methods: list containing at least on bw.methods-item
        perturb_input: dataframe containing input data for the perturbation analysis
        (output of the function *parameters_to_dataframe*)
        perturb_results: output of *perform_perturbation_analysis*
       
    returns:
        DataFrame containing sensitivity coefficients per parameter and impact category
    '''    
    delta_results={}

    for IC in LCIA_methods:
        delta_results_IC={}
        for i in perturb_results.index[1:]:
            delta_results_IC[i]=(perturb_results.loc[i,str(IC)]-perturb_results.loc['default',str(IC)])
        delta_results[str(IC)]=delta_results_IC    
    delta_results

    delta_parameter={}
    for i in perturb_input.index:
        delta_parameter[i]=(perturb_input.loc[i,'run'+str(i)]-perturb_input.loc[i,'default amount'])
    delta_parameter

    sensitivity_coefficient={}
    for IC in LCIA_methods:
        sensitivity_coefficient_IC={}
        for i in perturb_input.index:
            sensitivity_coefficient_IC[i]=delta_results[str(IC)]['run'+str(i)]/delta_parameter[i]
        sensitivity_coefficient[str(IC)]=sensitivity_coefficient_IC
    sensitivity_coefficient

    sensitivity_coefficient_df=pd.DataFrame()
    sensitivity_coefficient_df['from']=perturb_input['from']
    sensitivity_coefficient_df['from - code']=perturb_input['from - code']
    sensitivity_coefficient_df['from - location']=perturb_input['from - location']
    sensitivity_coefficient_df['to']=perturb_input['to']
    sensitivity_coefficient_df['to - code']=perturb_input['to - code']
    sensitivity_coefficient_df['type']=perturb_input['type']
    sensitivity_coefficient_df['category']=perturb_input['category']

    for i in sensitivity_coefficient_df.index:
        for IC in LCIA_methods:
            sensitivity_coefficient_df.loc[i,str(IC)]=sensitivity_coefficient[str(IC)][i]
    return sensitivity_coefficient_df




def plot_sensitivity_ratios_plotly(sensitivity_ratio_df, LCIA_method_names):
    '''arguments:
       sensitivity_ratio_df: pd.DataFrame containing sensitivity ratios
                             output of *calculate_sensitivity_ratios*
       LCIA_method_names: list with abbreveations for LCIA-method-names /
                          impact categories
       
       returns: nothing
           (A bar chart with sensitivity ratios per impact category is produced.
            The results are clustered in predefined categories.)'''
    plotly_df=pd.DataFrame()
    ind=0
    for p in sensitivity_ratio_df.index:
        for i,IC in enumerate(sensitivity_ratio_df.columns[7:]):
            plotly_df.loc[ind, 'Exchange']='FROM:'+sensitivity_ratio_df.loc[p,'from']+', TO:'+sensitivity_ratio_df.loc[p,'to']
            plotly_df.loc[ind, 'Category']=sensitivity_ratio_df.loc[p,'category']
            if LCIA_method_names==None:
                plotly_df.loc[ind, 'Impact Category']=IC
            else:
                plotly_df.loc[ind, 'Impact Category']=LCIA_method_names[i]
            plotly_df.loc[ind, 'Sensitivity Ratio [%]']=sensitivity_ratio_df.loc[p,IC]*100
            ind=ind+1
            
    ylimit_max=(round(plotly_df["Sensitivity Ratio [%]"].max()/10)+1)*10
    if plotly_df["Sensitivity Ratio [%]"].min() > 0:
        ylimit_min=0
    else:
        ylimit_min=(round(plotly_df["Sensitivity Ratio [%]"].min()/10)-1)*10
        
    fig = px.bar(plotly_df, y="Exchange", x="Sensitivity Ratio [%]", color="Category", orientation='h',
            animation_frame="Impact Category", template="simple_white",)
    fig.update_layout(#legend=dict(title=None, orientation="h", y=-0.4, yanchor="bottom", x=0.5, xanchor="center"),
                     #title=dict(y=0.9,x=0.5,xanchor='center', ),
                     font_family='Arial',
                     xaxis=dict(range=[ylimit_min, ylimit_max]),
                     hoverlabel=dict(bgcolor="white", font_size=10,font_family="Arial")
                        )
    fig["layout"].pop("updatemenus")
    fig.show()

    return




def plot_sensitivity_ratios(sensitivity_ratio_df,LCIA_methods,LCIA_method_names=None):
    '''
    arguments:  
        sensitivity_ratio_df: pd.DataFrame containing sensitivity ratios
                              output of *calculate_sensitivity_ratios*
        LCIA_methods: list with LCIA methods (bw.methods)
        LCIA_method_names: list with abbreveations for LCIA-method-names /
                           impact categories
       
    returns: nothing
        (A scatter plot with sensitivity ratios per impact category is produced.
         The results are clustered in predefined categories.)
    '''    
    if LCIA_method_names==None:
        LCIA_method_names=[str(m) for m in LCIA_methods]
    else:
        method_dict={}
        for m,meth in enumerate(LCIA_methods):
            method_dict[str(meth)]=LCIA_method_names[m]
            sensitivity_ratio_df=sensitivity_ratio_df.rename(columns=method_dict)
    
    markerstyles=["o","v","<",">","s","p","d","h","X"]
    
    indice_dict={}
    for cat in sensitivity_ratio_df['category'].unique():
        indice_dict[cat]=[i for i in sensitivity_ratio_df[sensitivity_ratio_df['category']==cat].index]
        
    key_numbers={}
    for n,k in enumerate(indice_dict.keys()):
        key_numbers[k]=n
    key_numbers

    fig, ax = plt.subplots()

    for i in sensitivity_ratio_df.index:
        for n,ind_list in enumerate(indice_dict.values()):
            if i in ind_list:
                ind_key=list(indice_dict.keys())[n]
                break
        n=key_numbers[ind_key]

        ax.scatter(LCIA_method_names,
                   (sensitivity_ratio_df.loc[i,LCIA_method_names].values.transpose()*100), 
                   label=ind_key,color=plt.get_cmap('Set1')(n), 
                   alpha=0.7, marker=markerstyles[n])
    ax.set_ylabel('Sensitivity Ratio [%]')
    #ax.set_ylim([0,100])
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='upper right', framealpha=1)
    fig.set_facecolor('white')
    fig.set_size_inches(10,6)
    
    return





def plot_sensitivity_ratios_with_hist(sensitivity_ratio_df,LCIA_methods,
                                      LCIA_method_names=None, hist_IC=0):
    '''
    arguments:  
        sensitivity_ratio_df: pd.DataFrame containing sensitivity ratios
                              output of *calculate_sensitivity_ratios*
        LCIA_methods: list with LCIA methods (bw.methods)
        LCIA_method_names: list with abbreveations for LCIA-method-names /
                           impact categories
        hist_IC: index of impact category displayed in the histogram
       
    returns: nothing
        (A scatter plot with sensitivity ratios per impact category is produced.
         Next to the scatter plot, a histogram is plotted showing the relative
         frequency of parameters in specific sensitivity ratio ranges.
         In the scatter plot the results are clustered in predefined categories.)
    '''    
    if LCIA_method_names==None:
        LCIA_method_names=[str(m) for m in LCIA_methods]
    else:
        method_dict={}
        for m,meth in enumerate(LCIA_methods):
            method_dict[str(meth)]=LCIA_method_names[m]
            sensitivity_ratio_df=sensitivity_ratio_df.rename(columns=method_dict)
    
    markerstyles=["o","v","<",">","s","p","d","h","X"]
    
    indice_dict={}
    for cat in sensitivity_ratio_df['category'].unique():
        indice_dict[cat]=[i for i in sensitivity_ratio_df[sensitivity_ratio_df['category']==cat].index]
        
    key_numbers={}
    for n,k in enumerate(indice_dict.keys()):
        key_numbers[k]=n
    key_numbers
    
    fig, (ax1,ax2) = plt.subplots(1,2,gridspec_kw={'width_ratios': [5, 1]})

    for i in sensitivity_ratio_df.index:
        for n,ind_list in enumerate(indice_dict.values()):
            if i in ind_list:
                ind_key=list(indice_dict.keys())[n]
                break
        n=key_numbers[ind_key]

        ax1.scatter(LCIA_method_names,(sensitivity_ratio_df.loc[i,LCIA_method_names].values.transpose()*100), 
                   label=ind_key,color=plt.get_cmap('Set1')(n), alpha=0.7, marker=markerstyles[n],s=30)


    ax1.set_ylabel('Sensitivity Ratio [%]')
    ax1.set_xlabel('Impact Category', labelpad=10)
    #ax1.set_ylim([0,100])
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    lgnd=ax1.legend(by_label.values(), by_label.keys(), loc='upper right', framealpha=1)
    #lgnd=ax1.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(0,-0.4,1,.1), ncol=3, loc='lower center', frameon=False, fontsize=12)

    for i,l in enumerate(lgnd.legendHandles):
        lgnd.legendHandles[i]._sizes = [30]

    #ax1.legend(by_label.values(), by_label.keys(), loc='upper right', framealpha=1)
    #histogram
    data=sensitivity_ratio_df[LCIA_method_names[hist_IC]].values
    weights = np.ones_like(data) / len(data)
    ax2.hist(data*100, weights=weights*100, orientation='horizontal', bins=50, log=True, color='black')
    ax2.set_ylim(ax1.get_ylim())
    #ax2.set_xlim([0.1,100])
    #ax2.set_title('GW', y=0.99, pad=-14)
    ax2.set_ylabel('Sensitivity Ratio [%] (absolute values)')
    ax2.set_xlabel('Relative Frequency [%] \n'+str(LCIA_method_names[hist_IC]))

    fig.set_facecolor('white')
    fig.set_size_inches(12,6)
    ax1.get_shared_y_axes().join(ax1, ax2)    
    return



def plot_sensitivity_ratios_absolute(sensitivity_ratio_df,LCIA_methods,LCIA_method_names=None):
    '''
    arguments:  
        sensitivity_ratio_df: pd.DataFrame containing sensitivity ratios
                              output of *calculate_sensitivity_ratios*
        LCIA_methods: list with LCIA methods (bw.methods)
        LCIA_method_names: list with abbreveations for LCIA-method-names /
                           impact categories
       
    returns: nothing
        (A scatter plot with sensitivity ratios per impact category is produced.
         The results are clustered in predefined categories.)
    ''' 
    if LCIA_method_names==None:
        LCIA_method_names=[str(m) for m in LCIA_methods]
    else:
        method_dict={}
        for m,meth in enumerate(LCIA_methods):
            method_dict[str(meth)]=LCIA_method_names[m]
            sensitivity_ratio_df=sensitivity_ratio_df.rename(columns=method_dict)
    
    markerstyles=["o","v","<",">","s","p","d","h","X"]
    
    indice_dict={}
    for cat in sensitivity_ratio_df['category'].unique():
        indice_dict[cat]=[i for i in sensitivity_ratio_df[sensitivity_ratio_df['category']==cat].index]
        
    key_numbers={}
    for n,k in enumerate(indice_dict.keys()):
        key_numbers[k]=n
    key_numbers

    fig, ax = plt.subplots()

    for i in sensitivity_ratio_df.index:
        for n,ind_list in enumerate(indice_dict.values()):
            if i in ind_list:
                ind_key=list(indice_dict.keys())[n]
                break
        n=key_numbers[ind_key]

        ax.scatter(LCIA_method_names,(sensitivity_ratio_df.loc[i,LCIA_method_names].values.transpose()*100), 
                   label=ind_key,color=plt.get_cmap('Set1')(n), alpha=0.7, marker=markerstyles[n])
    ax.set_ylabel('Sensitivity Ratio [%] (absolute values)')
    ax.set_ylim([0,100])
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='upper right', framealpha=1)
    fig.set_facecolor('white')
    fig.set_size_inches(10,6)
    
    return


def plot_sensitivity_ratios_with_hist_absolute(sensitivity_ratio_df,LCIA_methods,LCIA_method_names=None, hist_IC=0):
    '''
    arguments:  
        sensitivity_ratio_df: pd.DataFrame containing sensitivity ratios
                              output of *calculate_sensitivity_ratios*
        LCIA_methods: list with LCIA methods (bw.methods)
        LCIA_method_names: list with abbreveations for LCIA-method-names /
                           impact categories
        hist_IC: index of the LCIA_method to be displayed in the histogram
                 (0 refers to the first item of LCIA_method, ...)
       
    returns: nothing
        (A scatter plot with sensitivity ratios per impact category is produced.
         Next to the scatter plot, a histogram is plotted showing the relative
         frequency of parameters in specific sensitivity ratio ranges.
         In the scatter plot the results are clustered in predefined categories.)
        
    '''
    if LCIA_method_names==None:
        LCIA_method_names=[str(m) for m in LCIA_methods]
    else:
        method_dict={}
        for m,meth in enumerate(LCIA_methods):
            method_dict[str(meth)]=LCIA_method_names[m]
            sensitivity_ratio_df=sensitivity_ratio_df.rename(columns=method_dict)
    
    markerstyles=["o","v","<",">","s","p","d","h","X"]
    
    indice_dict={}
    for cat in sensitivity_ratio_df['category'].unique():
        indice_dict[cat]=[i for i in sensitivity_ratio_df[sensitivity_ratio_df['category']==cat].index]
        
    key_numbers={}
    for n,k in enumerate(indice_dict.keys()):
        key_numbers[k]=n
    key_numbers
    
    fig, (ax1,ax2) = plt.subplots(1,2,gridspec_kw={'width_ratios': [5, 1]})

    for i in sensitivity_ratio_df.index:
        for n,ind_list in enumerate(indice_dict.values()):
            if i in ind_list:
                ind_key=list(indice_dict.keys())[n]
                break
        n=key_numbers[ind_key]

        ax1.scatter(LCIA_method_names,abs(sensitivity_ratio_df.loc[i,LCIA_method_names].values.transpose()*100), 
                   label=ind_key,color=plt.get_cmap('Set1')(n), alpha=0.7, marker=markerstyles[n],s=30)


    ax1.set_ylabel('Sensitivity Ratio [%] (absolute values)')
    ax1.set_xlabel('Impact Category', labelpad=10)
 
    #ax1.set_ylim([0,100])
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    # plt.legend(by_label.values(), by_label.keys(), loc='upper right', framealpha=1)
    lgnd=ax1.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(0,-0.4,1,.1), ncol=3, loc='lower center', frameon=False, fontsize=12)
    
    for i,l in enumerate(lgnd.legendHandles):
        lgnd.legendHandles[i]._sizes = [30]
    
    #histogram
    data=abs(sensitivity_ratio_df[LCIA_method_names[hist_IC]]).values
    weights = np.ones_like(data) / len(data)
    ax2.hist(data*100, weights=weights*100, orientation='horizontal', bins=50, log=True, color='black')
    #ax2.set_ylim([0,100])
    ax2.set_ylabel('Sensitivity Ratio [%] (absolute values)')
    ax2.set_xlabel('Relative Frequency [%] \n'+str(LCIA_method_names[hist_IC]))
    
    fig.set_facecolor('white')
    fig.set_size_inches(12,8)
    ax1.get_shared_y_axes().join(ax1, ax2)     
    return


def top_sensitivity_ratios(sensitivity_ratio_df,top=None, above=0.1):
    '''
    arguments:  
        sensitivity_ratio_df: pd.DataFrame containing sensitivity ratios
                              output of *calculate_sensitivity_ratios*
        top: integer, number of highest scoring paramaters to be considered 
             per impact category
       
    returns: pd.DataFrame with highest scoring parameters per impact category
        
    '''    
    topx={}
    topx_set=[]
    for method in sensitivity_ratio_df.columns[7:]:
        topx_IC=[]
        sensitivity_ratio_IC_absolute=abs(sensitivity_ratio_df[method])
        sensitivity_ratio_df_sorted=sensitivity_ratio_IC_absolute.sort_values(ascending=False)
        if top!=None:
            for i in sensitivity_ratio_df_sorted[:top].index:    
                #if sensitivity_ratio_df_sorted[i] > 0.0:
                topx_IC.append(i)
                topx_set.append(i)
            topx[method]=topx_IC
        else:
            for i in sensitivity_ratio_df_sorted.index:
                if sensitivity_ratio_df_sorted.loc[i] >= above:
                    topx_IC.append(i)
                    topx_set.append(i)
            topx[method]=topx_IC
    topx_set=list(set(topx_set))  
    return sensitivity_ratio_df.loc[topx_set]


def plot_sensitivity_ratios_with_hist_absolute_with_legend(sensitivity_ratio_df,
                                                           LCIA_methods,
                                                           LCIA_method_names=None, 
                                                           hist_IC=0, 
                                                           top=None, 
                                                           SR_min=0.3):
    '''
    arguments:  
        sensitivity_ratio_df: pd.DataFrame containing sensitivity ratios
                              output of *calculate_sensitivity_ratios*
        LCIA_methods: list with LCIA methods (bw.methods)
        LCIA_method_names: list with abbreveations for LCIA-method-names /
                           impact categories
        hist_IC: index of the LCIA_method to be displayed in the histogram
                 (0 refers to the first item of LCIA_method, ...)
        top: number of top parameters per impact category to be labeled and
             explained in the legend, default: None
        SR_min: parameters with SR > SR_min are labeled and explained in the
                legend; SR_min is considered only, if top = None
       
    returns: legend
        (A scatter plot with sensitivity ratios per impact category is produced.
         Next to the scatter plot, a histogram is plotted showing the relative
         frequency of parameters in specific sensitivity ratio ranges.
         In the scatter plot the results are clustered in predefined categories.)
        
    '''
    if LCIA_method_names==None:
        LCIA_method_names=[str(m) for m in LCIA_methods]
    else:
        method_dict={}
        for m,meth in enumerate(LCIA_methods):
            method_dict[str(meth)]=LCIA_method_names[m]
            sensitivity_ratio_df=sensitivity_ratio_df.rename(columns=method_dict)

    topx={}
    topx_set=[]
    for method in sensitivity_ratio_df.columns[7:]:
        topx_IC=[]
        sensitivity_ratio_IC_absolute=abs(sensitivity_ratio_df[method])
        sensitivity_ratio_df_sorted=sensitivity_ratio_IC_absolute.sort_values(ascending=False)
        if top!=None:
            for i in sensitivity_ratio_df_sorted[:top].index:    
                topx_IC.append(i)
                topx_set.append(i)
            topx[method]=topx_IC
        else:
            for i in sensitivity_ratio_df_sorted.index:
                if sensitivity_ratio_df_sorted.loc[i] >= SR_min:
                    topx_IC.append(i)
                    topx_set.append(i)
            topx[method]=topx_IC
    topx_set=list(set(topx_set))  
    
    
    topx_list=[]
    topx_list_list=[*topx.values()]
    
    for l in topx_list_list:
        for i in l:
            topx_list.append(i)
    
    frequency_topx=dict(pd.Series(topx_list).value_counts())
    
    
    label={}
    
    for p,i in enumerate(frequency_topx.keys()):
        label[i]=p+1
    label
    
    legend=sensitivity_ratio_df.loc[topx_set,['from','to','category']]
    legend=legend.rename(index=label)
    
    for k in frequency_topx.keys():
        i=label[k]
        legend.loc[i,'frequency in top results']=str(frequency_topx[k])
        
    legend=legend.sort_index()
    
    
    markerstyles=["o","v","<",">","s","p","d","h","X"]
    
    if LCIA_method_names==None:
        LCIA_method_names=[str(m) for m in LCIA_methods]
    else:
        method_dict={}
        for m,meth in enumerate(LCIA_methods):
            method_dict[str(meth)]=LCIA_method_names[m]
            sensitivity_ratio_df=sensitivity_ratio_df.rename(columns=method_dict)
    
        
    indice_dict={}
    for cat in sensitivity_ratio_df['category'].unique():
        indice_dict[cat]=[i for i in sensitivity_ratio_df[sensitivity_ratio_df['category']==cat].index]
        
    key_numbers={}
    for n,k in enumerate(indice_dict.keys()):
        key_numbers[k]=n
        
    fig, (ax1,ax2) = plt.subplots(1,2,gridspec_kw={'width_ratios': [5, 1]})
            
    for i in sensitivity_ratio_df.index:
        for n,ind_list in enumerate(indice_dict.values()):
            if i in ind_list:
                ind_key=list(indice_dict.keys())[n]
                break
        n=key_numbers[ind_key]
    
        ax1.scatter(LCIA_method_names,abs(sensitivity_ratio_df.loc[i,LCIA_method_names].values.transpose()*100), 
                   label=ind_key,color=plt.get_cmap('Set1')(n), alpha=0.7, marker=markerstyles[n],s=30)
        
        
        for n,IC in enumerate(LCIA_method_names):
            if i in topx[IC]: 
                if i%2==0:
                    ax1.text(x=n+0.1, y=abs(sensitivity_ratio_df.loc[i,IC])*100-1,s=str(label[i]),fontsize=8)
                elif (i%3==0) & (i%2!=0):
                    ax1.text(x=n-0.3, y=abs(sensitivity_ratio_df.loc[i,IC])*100-1,s=str(label[i]),fontsize=8)
                else:
                    ax1.text(x=n+0.2, y=abs(sensitivity_ratio_df.loc[i,IC])*100-1,s=str(label[i]),fontsize=8)
    ax1.set_ylabel('Sensitivity Ratio [%] (absolute values)')
    ax1.set_xlabel('Impact Category', labelpad=10)
    #ax1.set_ylim([0,100])
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    # plt.legend(by_label.values(), by_label.keys(), loc='upper right', framealpha=1)
    lgnd=ax1.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(0,-0.4,1,.1), ncol=3, loc='lower center', frameon=False, fontsize=12)
    
    for i,l in enumerate(lgnd.legendHandles):
        lgnd.legendHandles[i]._sizes = [30]
    
    #histogram
    data=abs(sensitivity_ratio_df[LCIA_method_names[hist_IC]]).values
    weights = np.ones_like(data) / len(data)
    ax2.hist(data*100, weights=weights*100, orientation='horizontal', bins=50, log=True, color='black')
    #ax2.set_ylim([0,100])
    ax2.set_ylabel('Sensitivity Ratio [%] (absolute values)')
    ax2.set_xlabel('Relative Frequency [%] \n'+str(LCIA_method_names[hist_IC]))
    
    fig.set_facecolor('white')
    fig.set_size_inches(12,8)
    ax1.get_shared_y_axes().join(ax1, ax2)
    return legend