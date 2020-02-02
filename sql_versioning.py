from __future__ import absolute_import
import os
import json
import requests
from base64 import b64decode, b64encode
from io import open
import time
import logging

logging.basicConfig(format='%(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p',
                filename='sql_versioning.log',
                filemode='w',
                level=logging.INFO)

def save_file(path, cont):
	ff = open(path, 'w')
	ff.write(cont)
	ff.close()

def get_file(path):
	ff = open(path, 'r')
	cont = ff.read()
	ff.close()
	return cont

def version_file(filename, project_path,project_name, g_id, password, t_path, v_path):
	os.popen('cp ' + t_path + filename + ' ' + v_path + filename)
	os.popen('git -C ' + v_path + ' add ' + filename)
	os.popen('git -C ' + v_path + ' commit -m "' + filename + '"')

	path = os.getcwd()
	os.popen('rm -rf '+ path + '/' + "GtuDevOps")
	time.sleep(1)
	os.popen('git clone https://github.com/' + g_id + '/GtuDevOps.git')
	time.sleep(1)
	logging.info('Git Clone')
	if not os.path.exists(path + '/GtuDevOps/' + project_name):
		os.popen('mkdir '+ path + '/GtuDevOps/' + project_name)
	time.sleep(1)
	if os.path.exists(path + '/' + "GtuDevOps/"  + project_name + "/" + filename):
		os.popen('rm -f ' + path + '/' + "GtuDevOps/"  + project_name + "/" + filename)
	time.sleep(1)
	os.popen('cp -i '+ project_path + " " + path + '/' + "GtuDevOps/"  + project_name)
	time.sleep(1)
	logging.info('Copy file for repository')
	os.popen('git -C '+path+'/'+"GtuDevOps" + ' remote set-url origin https://'+g_id+':'+password+'@github.com/'+g_id+'/GtuDevOps.git')
	#os.popen('git -C '+path+'/'+"GtuDevOps/" + project_name+" pull")
	time.sleep(1)
	os.popen('git -C '+path+'/'+"GtuDevOps add " + project_name)
	time.sleep(1)
	logging.info('Git Add')
	os.popen('git -C '+path+'/' + "GtuDevOps/" + project_name+' commit -m "Versioning Successful"')
	logging.info('Git Commit')
	time.sleep(1)
	os.popen('git -C '+path+'/'+"GtuDevOps" + ' push -f -u origin master')
	logging.info('Git Push')
	time.sleep(1)

	os.popen('rm -f ' + t_path + '/' + filename)
	
def main(json_str):
	obj = json.loads(json_str)
	obj['destination'] = obj['origin']
	obj['name'] = obj['project_path'].split('/')[-1]

	if os.path.exists(obj['project_path']):

		if not os.path.exists('./sqlprojects'):
			os.popen('mkdir sqlprojects')
			os.popen("git init sqlprojects")

		if not os.path.exists('./sqlprojects/' + obj['project_name']):
			os.popen('mkdir '+ './sqlprojects/' + obj['project_name'])
			os.popen("git init " + './sqlprojects/' + obj['project_name'])

		if not os.path.exists('./sqlprojects/' + obj['project_name'] + '/temps/'):
			os.popen('mkdir '+ './sqlprojects/' + obj['project_name'] + '/temps')
			os.popen("git init " + './sqlprojects/' + obj['project_name'] + '/temps/')

		if not os.path.exists('./sqlprojects/' + obj['project_name'] + '/versions/'):
			os.popen('mkdir '+ './sqlprojects/' + obj['project_name'] + '/versions')
			os.popen("git init " + './sqlprojects/' + obj['project_name'] + '/versions/')

		t_path = './sqlprojects/' + obj['project_name'] + '/temps/'
		v_path = './sqlprojects/' + obj['project_name'] + '/versions/'

		if obj['origin'] == '2' and obj['op'] == "version":
			logging.info("Request is Version from Group-2.") 
			file_path = obj['project_path']
			decoded = get_file(file_path)
			save_file(t_path+obj['name'], decoded)
			is_exists = os.path.exists(v_path+obj['name'])
			if is_exists:
				logging.info(obj['name'] + ": Old Version Exists.")
				obj['destination'] = '9'
				decoded = get_file(t_path+obj['name'])
				obj['new'] = b64encode(str(decoded).encode('utf-8')).decode('utf-8')
				decoded = get_file(v_path+obj['name'])
				obj['old'] = b64encode(str(decoded).encode('utf-8')).decode('utf-8')
				obj['reminder'] = obj['origin']
				logging.info(obj['name'] + ": Old and New versions send to Group-9.")
			else:
				logging.info(obj['name'] + ": First Version.") 
				version_file(obj['name'], obj['project_path'], obj['project_name'], obj['github_login'], obj['github_password'], t_path, v_path)
				obj['result'] = "true"
				logging.info('Project Name: ' + obj['project_name'] + "\tFile Name: " + obj['name'] + '\nVersioning Successfully Completed. Send Result: true to Group-2')
		elif obj['origin'] == '9' and obj['op'] == "check":
			logging.info("Request is Check from Group-9.") 
			obj['destination'] = obj['reminder']
			if obj['result']:
				logging.info('Project Name: ' + obj['project_name'] + "\tFile Name: " + obj['name'] + 'Group-9 return true for versioning')
				version_file(obj['name'], obj['project_path'], obj['project_name'], obj['github_login'], obj['github_password'], t_path, v_path)
				obj['result'] = "true"
				logging.info('Versioning Successfully Completed. Send Result: true to Group-2')
			else:
				logging.info('Project Name: ' + obj['project_name'] + "\tFile Name: " + obj['name'] + 'Group-9 return false for versioning')
				obj['result'] = "false"
				logging.info('Versioning was not completed. Send Result: false to Group-2')
		else:
			obj['result'] = "false"
			logging.error('Request or Requester is not valid. Send Result: false to ' + obj['origin'] +'-Group.')
		obj['origin'] = '8'
		del obj['op']
		body = json.dumps(obj)
		logging.info('Send Request to ' + obj['destination'])
		requests.post("http://localhost:8081/", json=obj)
	else:
		logging.info('Project path does not exist. Send Result: false to ' + obj['origin'] +'-Group. Project Path: ' + obj['project_path'])
		obj['origin'] = '8'
		obj['result'] = "false"
		requests.post("http://localhost:8081/", json=obj)
main(json_str)