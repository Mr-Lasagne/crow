
"""
This is the main script to run the application.

"""
from multiprocessing import Process
from datetime import datetime
import os
import shutil
import logging
import subprocess
import re
import configparser
from flask import Flask, render_template, request, session
from flask_session import Session
import helper_functions as hf
import pandas as pd
from markupsafe import Markup
os.chdir('/home/cdsw/Clerical_Resolution_Online_Widget/flask_poc')

###some testing



start_time=datetime.now()

app=Flask(__name__)
logging.getLogger('werkzeug').disabled=True



config = configparser.ConfigParser()
config.read('config_flow.ini')
rec_id=config['id_variables']['record_id']
clust_id=config['id_variables']['cluster_id']
user = os.environ['HADOOP_USER_NAME']


#this clears the temporary folder
folder = f"{config['filespaces']['local_space']}"
for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))


#######################




app= Flask(__name__)
#may need to be something more secretive/encryptable! 
#app.config['SECRET_KEY']='abcd'
#app.config['SESSION_TYPE']='filesystem'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/', methods=['GET','POST'])
def welcome_page():
    """
    This page acts as a menu for the user
    
    """
    #session.clear()
    session['font_choice'] = f"font-family:{request.form.get('font_choice')}"
    session_keys=list(session)
    for i in session_keys: 
        if i!= 'font_choice':
            session.pop(i)
    return render_template("welcome_page.html", font_choice = session['font_choice'])


@app.route('/new_session', methods=['GET','POST'])
def new_session():
    """
    Allows the user to select their data, and launch the session
    """
    #code to remove session variables except for font choice
    #this is to ensure if the page is returned to in the same session- variables are cleared 
    #to avoid conflicts/saving over wrong files. 
    session_keys=list(session)
    for i in session_keys: 
        if i!= 'font_choice':
            session.pop(i)
    
    #using hadoop commands- get list of files in folder from hdfs 
    process = subprocess.Popen(["hadoop", "fs","-ls","-C",\
                                config['filespaces']['hdfs_folder'] ],\
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    std_out, std_error = process.communicate()
    std_out2=list(str(std_out).split('\\n'))
    
    #fix for error where first file in the folder has b' due to hadoop commands
    std_out2=[re.sub(r"^b'","",i) for i in std_out2 ]
    
    button = request.form.get("hdfs")
    config_status = request.form.get("config")
    version = request.form.get("version")
    return render_template("new_session.html", button=button,
                                              version=version,
                                              config_status=config_status, std_out=std_out2,
                                              font_choice = session['font_choice'])


@app.route('/cluster_version', methods=['GET','POST'])
def index():
    """
    This is the main page where clerical happens! 
    """
    #When cluster version button pressed. Remove font_choice from session variables.
    if request.form.get('version')=="Cluster Version":
        session_keys=list(session)
        for i in session_keys: 
            if i!= 'font_choice':
                session.pop(i)


      
      
    if 'full_path' not in session:
        #print('running if 1')
        #actions for if this is the initial launch/path is not a session variable 
        #get the hdfs file paths and file name
        session['full_path']=str(request.form.get("file_path"))
        session['filename']=session['full_path'].split('/')[-1]

        #get the temporary file location from config
        temp_local_path=f"{config['filespaces']['local_space']+session['filename']}"
        #get the data from hdfs into local location
        hf.get_hadoop(session['full_path'],temp_local_path)

        #load from local location to a pandas df
        local_file=pd.read_parquet(temp_local_path)

        #validate pd columns/raise errors
        hf.validate_columns(local_file)

        #if temp path is now a directory; remove directory 
        if os.path.isdir(temp_local_path):
            shutil.rmtree(temp_local_path)
            #this is a hack to resolve; to_parquet only works with single partition files.
        #save back to temp path as a one-partition parquet
        local_file.to_parquet(temp_local_path)

        #create json version of the local file (a flask hack)
        session['working_file']=local_file.to_json()

        #if there are not already; create a match column and sequential_id column
        if 'Match' not in local_file.columns: 
            local_file['Match']='[]'
        if 'Sequential_Cluster_Id' not in local_file.columns: 
            local_file['Sequential_Cluster_Id'] = pd.factorize(local_file[clust_id])[0]
            local_file=local_file.sort_values(by=['Sequential_Cluster_Id'])

        if 'Comment' not in local_file.columns: 
            local_file['Comment']=''
       
        if 'Sequential_Record_Id' not in local_file.columns: 
            local_file['Sequential_Record_Id'] = pd.factorize(local_file[rec_id])[0]
            local_file=local_file.sort_values(by=['Sequential_Record_Id'])
            
        
        if 'Sequential_Cluster_Id' not in local_file.columns: 
            local_file['Sequential_Cluster_Id'] = pd.factorize(local_file[clust_id])[0]
            local_file=local_file.sort_values('Sequential_Cluster_Id').sort_values(by=['Sequential_Cluster_Id'])



        #get the local filepath in_prog and done paths rename locally to in_prog_path
        local_in_prog_path, local_filepath_done=hf.get_save_paths(temp_local_path,temp_local_path\
                                                                  .split('/'))
        os.rename(temp_local_path, local_in_prog_path)

        #get the hdfs filepath in_prog and done paths and rename in hdfs to in_prog_path
        hdfs_in_prog_path, hdfs_filepath_done=hf.get_save_paths(session['full_path'],\
                                                                session['full_path'].split('/'))
        #start the save thread to move in progress file back to hdfs. 
        s_thread=Process(target=save_thread, args= (local_in_prog_path,\
                                              hdfs_in_prog_path,\
                                              local_file, local_filepath_done, hdfs_filepath_done))
        s_thread.start()

    else: 
        #print('running if 2')
        #actions for every time the page is re-loaded. 
        #read session variable json to pandas
        local_file=pd.read_json(session['working_file']).sort_values(by=['Sequential_Record_Id'])
        #set temp loaction 
        temp_local_path=f"{config['filespaces']['local_space']+session['filename']}"

        #get the local filepath in_prog and done paths rename locally to in_prog_path
        local_in_prog_path, local_filepath_done=hf.get_save_paths(temp_local_path,\
                                                                  temp_local_path.split('/'))

        #get the hdfs filepath in_prog and done paths and rename in hdfs to in_prog_path
        hdfs_in_prog_path, hdfs_filepath_done=hf.get_save_paths(session['full_path'],\
                                                                session['full_path'].split('/'))

    #set the index variable. This is the iterator that controls the flow of the application as you move through clusters. 
    #it is a sequential integer created based on the cluster id.
      
      ############ session variables and toggles#############
      
    if 'index' not in session:
        session['index']=int(local_file['Sequential_Cluster_Id'][(local_file.Match.values == '[]').argmax()])

    #set select all toggle
    if "select_all" not in session: 
        session['select_all']=0

    #highlight differences toggle    
    if 'highlight_differences' not in session: 
        session['highlight_differences']=0

    if hf.check_matching_done(local_file):
        local_file.to_parquet(local_filepath_done)
    else:
        local_file.to_parquet(local_in_prog_path)
        

    
      ##############################Button Code###############################
      ##Code to control the actions on each button press.
      #if match button pressed; add the record Id's of the 
      #selected records to the match column as an embedded list
    
    match_error=''
    if request.form.get('Match')=="Match":
    #if match button pressed. 
            #get a list of cluster ids that are currently selected
        cluster = request.form.getlist("cluster")
        for i in cluster:
            if len(cluster)<=1:
                match_error='you have only selected one record'
            elif len(cluster)>=2:
                local_file.loc[local_file[rec_id]==i,'Match']=str(cluster)
                local_file.loc[local_file[rec_id]==i,'Comment']=str(request.form.get("Comment"))

        #move on to next cluster if not at end of file
                if local_file.Sequential_Cluster_Id.nunique()>int(session['index'])+1:
                    hf.advance_cluster(local_file)

                #save if at a backup_save checkpoint.
                if session['index'] % int(config['custom_setting']['backup_save'])==0:
                    s_thread=Process(target=save_thread, args= (local_in_prog_path,hdfs_in_prog_path,\
                                                          local_file, local_filepath_done,\
                                                          hdfs_filepath_done))
                    s_thread.start()

              
             
    elif request.form.get('Non-Match')=="Non-Match":
    #if non-match button pressed. 

        cluster = request.form.getlist("cluster")
        for i in cluster:
            local_file.loc[local_file[rec_id]==i,'Match']=f"['No Match In Cluster For {i}']"
            local_file.loc[local_file[rec_id]==i,'Comment']=str(request.form.get("Comment"))

        #move on to next cluster if at the end of a file
        if local_file.Sequential_Cluster_Id.nunique()>int(session['index'])+1:
            hf.advance_cluster(local_file)

        ##save if at a backup_save checkpoint.
        if session['index'] % int(config['custom_setting']['backup_save'])==0:
            s_thread=Process(target=save_thread, args= (local_in_prog_path,hdfs_in_prog_path,\
                                                  local_file, local_filepath_done, \
                                                  hdfs_filepath_done))
            s_thread.start()

              
    #if Clear-Cluster pressed; replace the match column for cluster with '[]'
    if request.form.get('Clear-Cluster')=="Clear-Cluster":
        cluster_ids=list(local_file.loc[local_file['Sequential_Cluster_Id']==session['index']][rec_id].values)
        for  i in cluster_ids:
            local_file.loc[local_file[rec_id]==i,'Match']='[]'
            local_file.loc[local_file[rec_id]==i,'Comment']=''


    #if back button pressed; set session['index'] back to move to previous cluster (Unless index=0)
    if request.form.get('back')=="back":
        if int(session['index'])>0:
            session['index'] = session['index']-1

    #if save pressed...save file to hdfs    
    if request.form.get('save')=="save":
        s_thread=Process(target=save_thread, args= (local_in_prog_path,hdfs_in_prog_path, local_file, local_filepath_done, hdfs_filepath_done))
        s_thread.start()


    if request.form.get('selectall')=="selectall":
        print(session['select_all'])
        if session['select_all']==1:
            session['select_all']=0
        elif session['select_all']==0:
            session['select_all']=1
       
    if request.form.get('highlight_differences') == 'highlight_differences':
        if session['highlight_differences']==1:
            session['highlight_differences']=0
        elif session['highlight_differences']==0:
            session['highlight_differences']=1
            print('highlighter_on')
      
        
      ####################Things to display code#########################
      
    #extract a df dor the current cluster
    data_f=local_file.loc[local_file['Sequential_Cluster_Id']==session['index']]

    #select columns; split into column headers and data
    #possible copy set warning place
    display_cols_list=[config['display_columns'][i] for i in config['display_columns']]+["Match","Comment"]
    df_display=data_f[display_cols_list].copy()
    #print(df_display)
    highlight_cols=[config['display_columns'][i] for i in config['display_columns']]
    #possiple copy set warning place
    df_display[highlight_cols] = df_display[highlight_cols].astype(str)
    highlight_cols.remove(rec_id)
    

      
      ################HIGHLIGHTER###############
    

    if session['highlight_differences']==1: 

        for column in highlight_cols:
            for i in df_display.index.values[1:]:
                output = []
                element = df_display.loc[i,column]
                for count, letter in enumerate(element):
                    if count<= len(df_display.loc[df_display.index.values[0],column])-1:
                        if letter != df_display.loc[df_display.index.values[0],column][count] :
                            output.append("<mark>"+ letter + "</mark>")
                        else:  
                            output.append(letter)
                    #except:
                    else:
                        output.append("<mark>"+ letter + "</mark>")

                    data_point = ''.join(output)

                df_display.loc[i,column] = Markup(data_point)

      
    columns = df_display.columns
    data = df_display.values

      
      #############OTHER THINGS TO DISPLAY#######
      

    #get number of clusters and message to display. 
    num_clusters=str(local_file.Sequential_Cluster_Id.nunique())
    display_message=config['message_for_matchers']['message_to_display']
    id_col_index=df_display.columns.get_loc(rec_id)
    #cast local_file back to json
    session['working_file']=local_file.to_json()
    match_col_index=df_display.columns.get_loc('Match')
        
    #check if cluster done 
    cur_cluster_done= hf.check_cluster_done(local_file)

    #set continuation message
    not_last_record=local_file.Sequential_Cluster_Id.nunique()>int(session['index'])+1
    if (not_last_record is True) or cur_cluster_done is False:
        done_message='Keep Matching'
    elif (not_last_record is False) and cur_cluster_done is True:
        done_message='Matching Finished- Press save and close the application'
    

    column_width = len(columns)+1
    button_left = int(column_width/2)
    button_right = button_left + 2*(column_width / 2 - int(column_width / 2))
    

    return  render_template("cluster_version.html",
                            data = data,
                            columns=columns, cluster_number=str(int(session['index']+1)),\
                            button_left = button_left, button_right = button_right,\
                            num_clusters=num_clusters, display_message=display_message, \
                            done_message=done_message, id_col_index=id_col_index,\
                            select_all=session['select_all'],\
                            highlight_differences=session['highlight_differences'],\
                            font_choice = session['font_choice'],\
                            match_error=match_error, match_col_index=match_col_index)

    
    

    
    

@app.route('/about_page', methods=['GET','POST'])
def about():
    """
    This page gives info and guidance about the app
    """
    return render_template("about_page.html")
  



#########################
#########################
if __name__=='__main__':  
    
    
    def save_thread(local_in_prog_path,hdfs_in_prog_path,\
                    local_file, local_filepath_done, hdfs_filepath_done):
        """
        A fumctiom to save to hdfs
        """
        hf.remove_hadoop(session['full_path'])
        hf.remove_hadoop(hdfs_in_prog_path)
        hf.remove_hadoop(hdfs_filepath_done)
        if os.path.exists(local_in_prog_path):
            os.remove(local_in_prog_path)
            print(f'{local_in_prog_path} deleted')
        else:
            print(f'{local_in_prog_path} NOT deleted')
            
        if os.path.exists(local_filepath_done): 
            os.remove(local_filepath_done)
            print(f'{local_filepath_done} deleted')
        else:
            print(f'{local_filepath_done} NOT deleted')
        
        
              
    
        if hf.check_matching_done(local_file):
            local_file.to_parquet(local_filepath_done)
            hf.save_hadoop(local_filepath_done,hdfs_filepath_done)

        else:
            local_file.to_parquet(local_in_prog_path)
            hf.save_hadoop(local_in_prog_path,hdfs_in_prog_path)
            
        print('Saving Complete')
             
    def run_app():
        """
        A function to run the main app
        """
        print('App is running, press icon in top corner to launch application.\n\
              It may take a few secounds for the "CROW clerical tool" icon to appear.\n\
              if you cannot see it, look again in a few secounds')

        app.config["TEMPLATES_AUTO_RELOAD"] = True
        app.run(host=os.getenv('CDSW_IP_ADDRESS'),port= int(os.getenv('CDSW_PUBLIC_PORT')))
        

    ra=Process(target=run_app)
    ra.start()
    
    #run a timer in the main terminal
    #this is run in main occupying the kernel; but timesout after a set time
    
    nowtime=datetime.now()
    n=(nowtime-start_time).total_seconds()
    while n < 3600:
        nowtime=datetime.now()
        n=(nowtime-start_time).total_seconds()
    ra.terminate()
    print('Session has timed out. Please re-start your session \n and re-run the script to continue')





    
