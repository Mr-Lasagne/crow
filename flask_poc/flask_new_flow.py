#note file relates to templates 2 folder in git 

import pandas as pd
import logging
from flask import Flask, render_template, request, redirect, \
url_for, flash, make_response, session, jsonify
import os
import ast
import numpy as np
from dlh_utils import sessions
from dlh_utils import utilities
import configparser
import getpass
import pwd


os.chdir('/home/cdsw/Clerical_Resolution_Online_Widget/flask_poc')
app=Flask(__name__)
logging.getLogger('werkzeug').disabled=True

spark=sessions.getOrCreateSparkSession(appName='crow_test', size='medium')
config = configparser.ConfigParser()
config.read('config_flow.ini')
rec_id=config['id_variables']['record_id']
clust_id=config['id_variables']['cluster_id']
file=spark.sql(f"SELECT * FROM {config['filepath']['file']}")
user = os.environ['HADOOP_USER_NAME']



working_file=file.toPandas()
#this line not working
#working_file = working_file.sort_values(by = clust_id).reset_index().astype(str)

#fill nulls in match column with '[]'.This is just to enable the advance cluster function, as is to work
#could probably be improved so we don't have to do this.
#renaming. 

if 'Match' not in working_file.columns: 
  working_file['Match']='[]'
  print('hi')
  
if 'Sequential_Cluster_Id' not in working_file.columns: 
    working_file['Sequential_Cluster_Id'] = pd.factorize(working_file[clust_id])[0]
working_file=working_file.sort_values('Sequential_Cluster_Id')


origin_file_path=config['filepath']['file']
origin_file_path_fl=config['filepath']['file'].split('.')


#######################
#####working poc#######
#######################

##################
##HELPER FUNCTIONS
##################
#Note will probably eventually move these into a separate script



(working_file.Match.values != 'a').argmax()
def advance_cluster():
  #note this function is very clunky and could likely be improved. 
  """
  1)A Function to: determine the number of matches made in a given cluster
  2)If 1 or 0 unmatcher records in cluster remain; progress to the next cluster. 
  
  Parameters: None
  Returns: None
  
  """
  num_in_cluster=len(working_file.loc[working_file['Sequential_Cluster_Id']==session['index']])
  print(num_in_cluster)
  list_decided=[set(ast.literal_eval(i)) for i in working_file.loc[working_file['Sequential_Cluster_Id']==session['index']]['Match']]
  print(list_decided)
  uni_set_decided={x for l in list_decided for x in l}
  print(uni_set_decided)
  num_decided=len(uni_set_decided)
  if (num_in_cluster-num_decided)<=1:
      for r_id in [x for x in working_file.loc[working_file['Sequential_Cluster_Id']==session['index']][rec_id] if x not in uni_set_decided]: 
            working_file.loc[working_file[rec_id]==r_id,'Match']=f"['No Match In Cluster For {r_id}']"
      session['index'] = int(session['index'])+ 1
      
def check_matching_done(df=working_file): 
  if len(working_file[working_file.Match == '[]'])>0: 
    return 0
  if len(working_file[working_file.Match == '[]'])==0:
    print('matching_done')
    return 1
  
def save_rename_hive(dataframe, old_path,new_path):
    sparkDF=spark.createDataFrame(dataframe)
    sparkDF.registerTempTable("temp_table")
    spark.sql(f"""DROP TABLE IF EXISTS {old_path}""")
    #unhash to delete after new table created 
    spark.sql(f"""CREATE TABLE IF NOT EXISTS {new_path} AS SELECT * FROM temp_table""")
    
#################################################
#################filepaths#######################
#################################################

if 'inProgress' in origin_file_path_fl[-1]:
        
        # If it is the same user
        if (user in origin_file_path_fl[-1]):
            # Dont rename the file
            in_prog_path= origin_file_path
            end_file_name=origin_file_path_fl[-1][:-11]+'_DONE'
            # create the filepath name for when the file is finished
            filepath_done = ".".join([origin_file_path_fl[0], end_file_name])
        else:
            
            print('USER_NOT_IN_NAME')

            # Rename the file to contain the additional user
            in_prog_path = origin_file_path_fl[-1][:-11]+f'_{user}'+'_inProgress'
            
            
            end_file_name=origin_file_path_fl[-1][:-11]+f'_{user}'+'_DONE'
            filepath_done=".".join([origin_file_path_fl[0],end_file_name ])
 
                               
    # If a user is picking this file again and its done
elif 'DONE' in origin_file_path_fl[-1]:
        
        # If it is the same user
        if (user in origin_file_path_fl[-1]):
            # dont change filepath done - keep it as it is
            filepath_done = config['filepath']['file']
        
            # Rename the file 
            in_prog_path=".".join([origin_file_path_fl[0],origin_file_path_fl[-1][:-5]+'_inProgress'])

            
        else:
            # If it is a different user
            # Rename the file to include the additional user
            in_prog_path=".".join([origin_file_path_fl[0],origin_file_path_fl[-1][:-5]+f'_{user}'+'_inProgress'])

            # create the filepath done
            filepath_done=".".join([origin_file_path_fl[0],in_prog_path[:-11]+'_DONE' ])
            
else:
      
        in_prog_path=".".join([origin_file_path_fl[0],origin_file_path_fl[-1]+f'_{user}'+'_inProgress' ])



save_rename_hive(working_file, origin_file_path, in_prog_path) 

  
      
      


#######################
app= Flask(__name__)
#may need to be something more secretive/encryptable! 
app.config['SECRET_KEY']='abcd'


@app.route('/', methods=['GET','POST'])
def welcome_page():
    return render_template("welcome_page.html")

@app.route('/new_session', methods=['GET','POST'])
def new_session():
   # session['input_df']=data_pd
    button = request.form.get("hdfs")
    config_status = request.form.get("config")
    version = request.form.get("version")

    return render_template("new_session.html", button=button,
                                              version=version,
                                              config_status=config_status)

@app.route('/load_session', methods=['GET','POST'])
def load_session():
    directory = os.listdir('saved_sessions')
    
    return render_template('load_session.html', directory=directory)

@app.route('/cluster_version', methods=['GET','POST'])
def index(): 
      #set highlighter toggle to 0
      session['highlighter']=False
      #problem; this needs to only be ran when app first opened
      if 'index' not in session:
              session['index']=int(working_file['Sequential_Cluster_Id'][(working_file.Match.values == '[]').argmax()])
              print(session['index'])

      else:
              print(f"{session['index']} newsesh")
      
      if {'Match'}.issubset(working_file.columns):
            pass
            # variable indicates whether user has returned to this file (1) or not (0)
        
      else:
            
            # create a match column and fill with blanks
            #working_file['Match'] = ''
            pass
      if request.form.get('Match')=="Match":
              cluster = request.form.getlist("cluster")
              print(cluster)
              for i in cluster:
                  #note resident ID will need to change from to be read from a config as any reccord id 
                  working_file.loc[working_file[rec_id]==i,'Match']=str(cluster)
              advance_cluster()
            

      elif request.form.get('Non-Match')=="Non-Match":
              #note this section needs building out. 
              #working_file.loc[working_file['Sequential_Cluster_Id']==session['index'],'Match']=0
              cluster = request.form.getlist("cluster")
              for i in cluster:
                  #note resident ID will need to change from to be read from a config as any reccord id 
                  working_file.loc[working_file[rec_id]==i,'Match']=f"['No Match In Cluster For {i}']"
              advance_cluster()
              
              
              

      if request.form.get('back')=="back":
              session['index'] = session['index']-1

      if request.form.get('save')=="save":
              if check_matching_done(): 
                  print('matching_done')
                  save_rename_hive(working_file, in_prog_path, filepath_done)
              else: 
                  save_rename_hive(working_file, in_prog_path, in_prog_path)
              print('save activated ')

      
      if 'index' not in working_file.columns:
          index = (list(range(max(working_file.count()))))
          working_file.insert(0,'index',index)
      else:
          pass
      #not WORKIng 
      df=working_file.loc[working_file['Sequential_Cluster_Id']==session['index']]
      cols_list=[config['display_columns'][var] for var in config['display_columns']]

      columns = df.columns
      data = df.values
      num_clusters=str(working_file.Sequential_Cluster_Id.nunique())
      display_message=config['message_for_matchers']['message_to_display']

      return  render_template("cluster_version.html",
                              data = data,
                              columns=columns, cluster_number=session['index'], num_clusters=num_clusters, display_message=display_message)

    
    
    
    
    
    
    
@app.route('/pairwise_version', methods=['GET','POST'])
def index_pairwise(): 
      #set highlighter toggle to 0
      session['highlighter']=False
      if 'index' not in session:
              session['index']=int(working_file['Sequential_Cluster_Id'][0])

      else: 
        pass
        #logic to display firdt unlinked record first. 

      cluster = request.form.getlist("cluster")
      
      # df=working_file.loc[working_file['Sequential_Cluster_Id']==session['index']]
      # session['index'] = int(session['index'])+ 1

      if request.form.get('Match')=="Match":
              working_file.iloc[cluster]['Match']=1
              session['index'] = int(session['index'])+ 1
              check_matching_done()

      elif request.form.get('Non-Match')=="Non-Match":
              working_file.loc[working_file['Sequential_Cluster_Id']==session['index'],'Match']=0
              session['index'] = int(session['index'])+ 1

      if request.form.get('back')=="back":
              print('back')
              session['index'] = int(session['index'])-1

      if request.form.get('save')=="save":
              save_output()






      df=working_file.loc[working_file['Sequential_Cluster_Id']==session['index']]
      index = (list(range(max(df.count()))))
      df.insert(0,'index',index)

      
      columns = df.columns
      data = zip(df.values, index)
      session['index'] = int(session['index'])+ 1
      return  render_template("cluster_version.html",
                              data = data,
                              columns=columns)

@app.route('/about_page', methods=['GET','POST'])
def about():
    return render_template("about_page.html")

#########################
#########################


app.config["TEMPLATES_AUTO_RELOAD"] = True
app.run(host=os.getenv('CDSW_IP_ADDRESS'),port= int(os.getenv('CDSW_PUBLIC_PORT')))