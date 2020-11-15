from flask import Flask, request
from waitress import serve
from hashlib import sha256
from json import loads, dumps
from datetime import datetime
from os import path, rename
from time import time
from re import match, findall

app = Flask(__name__)
datastore = "datastore.txt"
metricsstore = "metrics.txt"
logfile = "server.log"

#
# Post a message
#
@app.route("/messages",methods = ["POST"])
def postMessage():
	request_received_time = getDateTime()
	client_ip = request.remote_addr
	msg = request.json["message"]
	key = sha256(msg.encode('utf-8')).hexdigest()
	if existsMessage(key) == []:
		try:
			with open(datastore, "a") as fw:
				fw.write(key + "," + msg + "\n")
				fw.close()
				writeMetrics(request_received_time,client_ip,"POST",200,"success", "/messages")
				writeLog(' '.join([request_received_time,client_ip,"POST","200","success"]) + " Message: " + msg + " Digest: " + key)
				return dumps({"digest" : key}, indent=4), 200
		except:
			writeMetrics(request_received_time,client_ip,"POST",422,"error", "/messages")
			writeLog(' '.join([request_received_time,client_ip,"POST","422","error"]) + " Message: " + msg + " Digest: " + key)
			return dumps({ "error": "unable to process message", "message" : msg }, indent=4), 422
	else:
		writeMetrics(request_received_time,client_ip,"POST",422,"error", "/messages")
		writeLog(' '.join([request_received_time,client_ip,"POST","422","error"]) + " Message: " + msg + " Digest: " + key)
		return dumps({ "error": "unable to process message, message already exists", "message" : msg }, indent=4), 422

#
# Get message corresponding to digest if exists, else return error
#
@app.route("/messages/<hash>",methods = ["GET"])
def getMessage(hash):
	request_received_time = getDateTime()
	client_ip = request.remote_addr
	shash = str(hash)
	message_line = existsMessage(hash)
	if message_line != []:
		writeMetrics(request_received_time,client_ip,"GET",200,"success", "/messages/" + shash)
		writeLog(' '.join([request_received_time,client_ip,"GET","200","success"]) + " Message :" +  message_line[0] + " Digest: " + shash)
		return dumps({"message" : message_line[0]}, indent=4), 200
	else:
		writeMetrics(request_received_time,client_ip,"GET",404,"error", "/messages/" + shash)
		writeLog(' '.join([request_received_time,client_ip,"GET","404","error"]) +  " Digest: " + shash)
		return dumps({ "error": "unable to find message", "message_sha256" : hash }, indent=4), 404


#
# Delete message and digest if exists, else return error.
#
@app.route("/messages/<hash>",methods = ["DELETE"])
def deleteMessage(hash):
	request_received_time = getDateTime()
	client_ip = request.remote_addr
	shash = str(hash)
	message_line = existsMessage(hash)
	if message_line != []:
		try:
			fw = open("temp.txt", "w")
			lnum = 1
			for line in open(datastore, "r"):
				if lnum != message_line[1]:
					fw.write(line)
				lnum += 1
			fw.close()
			rename("temp.txt", datastore)	
			writeMetrics(request_received_time,client_ip,"DELETE",200,"success", "/messages/" + shash)
			writeLog(' '.join([request_received_time,client_ip,"DELETE","200","success"]) + " Message :" +  message_line[0] + " Digest: " + shash)
			return dumps({ "success": "Deleted message", "message_sha256" : hash }, indent=4), 200
		except:
			writeMetrics(request_received_time,client_ip,"DELETE",404,"error", "/messages/" + shash)
			writeLog(' '.join([request_received_time,client_ip,"DELETE","404","error"]) + " Digest: " + shash)
			return dumps({ "error": "unable to delete message", "message_sha256" : hash }, indent=4), 404
	else:
		writeMetrics(request_received_time,client_ip,"DELETE",404,"error", "/messages/" + shash)
		writeLog(' '.join([request_received_time,client_ip,"DELETE","404","error"]) + " Digest: " + shash)
		return dumps({ "error": "unable to find message", "message_sha256" : hash }, indent=4), 200

#
# Get metrics
#
@app.route("/metrics",methods = ["GET"])
def getMetrics():
	metrics = {}
	res_time_arr = []
	response_time = 0.0
	metrics_val = {}
	date = ""
	for line in open(metricsstore, "r"):
		if findall("\w.*\d{2}:\d{2}:\d{2}", line) != []:
			line_arr = line.split()
			date = ' '.join(line_arr[:4])
			metrics_val = {"time": line_arr[4], "source_ip": line_arr[5], "method": line_arr[6], "status_code": line_arr[7], \
					"status_message": line_arr[8], "url": line_arr[9]}
			res_time_arr.append(metrics_val)
		elif "Start Time:" in line:
			res_time_arr.append(float(line.split()[-1]))
		elif "End Time:" in line:
			end_time = float(line.split()[-1])
			if isinstance(res_time_arr[-1], dict):
				response_time = str(round((end_time - res_time_arr[0]) * 1000, 2)) + " milliseconds"
				metrics_val["response_time"] = response_time
				if date not in metrics.keys():
					metrics[date] = [metrics_val]
				else:
					metrics[date].append(metrics_val)
			res_time_arr = []
			response_time = 0.0
			metrics_val = {}
			date = ""
	for key in metrics.keys():
		stats = {}
		methods = {}
		total_time, avg_res_time = 0, 0
		for val in metrics[key]:
			if val["status_code"] not in stats.keys():
				stats[val["status_code"]] = 1
			else:
				stats[val["status_code"]] += 1
			if val["method"] not in methods.keys():
				methods[val["method"]] = 1
			else:
				methods[val["method"]] += 1
			total_time += float(val["response_time"].split()[0])
		avg_res_time = round(total_time/len(metrics[key]), 2)
		metrics[key] = {"total_requests_count": len(metrics[key]), "all reqests": metrics[key], "status_counts": stats, \
				"method_counts": methods, "Average Response Time":str(avg_res_time) + " milliseconds"}
	writeLog(getDateTime() + " GET /metrics")
	writeLog("Dates :" + str(metrics.keys()))
	writeLog("Metrics :" + str(metrics.values()))
	return dumps(metrics, indent=4), 200			
	

#
# Find if message exist in Datastore
#
def existsMessage(hash):
	msg_exists = False
	if not path.isfile(datastore):
                return []
	else:	
		line_number = 0
		for line in open(datastore, "r"):
			line_number += 1
			digest_message = line.split(",")[:2]
			if hash == digest_message[0]:
				msg_exists = True
				return [digest_message[1][:-1], line_number]
		if msg_exists == False:
			return []


#
# Write metrics
#
def writeMetrics(date_time,client_ip,method,status_code,status_message,url,time=""):
	with open(metricsstore, "a") as fw:
		message = ' '.join([date_time, client_ip, method, str(status_code), status_message,url,time])
		fw.write(message + "\n")
	fw.close()

#
# Write logs
#
def writeLog(message):
	with open(logfile, "a") as fw:
		fw.write(message + "\n")
	fw.close()

#
# Get current date and time
#
def getDateTime():
	return datetime.now().strftime("%A, %d. %B %Y %H:%M:%S %Z")

# Before request
@app.before_request
def before_request():
	writeMetrics("","","",0,"","","Start Time: " + str(time()))

# Teardone request
@app.teardown_request
def teardown_request(exception=None):
	writeMetrics("","","",0,"","","End Time: " + str(time())) 

	
#
# Start the server on port 8080
#
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
