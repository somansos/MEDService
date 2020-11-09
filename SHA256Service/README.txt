Setup Instructions and Test Cases 

1. Running Service in docker container

Setup Instructions

$ unzip SHA256Service.zip
Archive:  SHA256Service.zip
   creating: SHA256Service/
  inflating: SHA256Service/.DS_Store  
  inflating: __MACOSX/SHA256Service/._.DS_Store  
  inflating: SHA256Service/requirements.txt  
  inflating: SHA256Service/Dockerfile  
  inflating: SHA256Service/README.txt  
   creating: SHA256Service/src/
  inflating: SHA256Service/src/SHA256Server.py  
$ 

$ cd SHA256Service/
$ docker build -t sha256serviceimage .
Sending build context to Docker daemon  28.67kB
Step 1/6 : FROM python:3.9
 ---> 768307cdb962
Step 2/6 : WORKDIR /code
 ---> Using cache
 ---> 29d1e56ff268
Step 3/6 : COPY requirements.txt .
 ---> Using cache
 ---> 93e8d1f7445f
Step 4/6 : RUN pip3 install -r requirements.txt
 ---> Using cache
 ---> fbe5481c6d1c
Step 5/6 : COPY src/ .
 ---> 668c096a0021
Step 6/6 : CMD [ "python3", "./SHA256Server.py" ]
 ---> Running in 4a8c111d40b6
Removing intermediate container 4a8c111d40b6
 ---> 989018e1418a
Successfully built 989018e1418a
Successfully tagged sha256serviceimage:latest
$ 


$ docker images
REPOSITORY                                  TAG                 IMAGE ID            CREATED              SIZE
sha256serviceimage                          latest              989018e1418a        About a minute ago   897MB
$ 

$ docker run -d -p 8080:8080 sha256serviceimage
84326b56f7ebe40527b8db7776c38131265145a342d049d2ac27bff8181bfd6c
$ 

$ docker ps
CONTAINER ID        IMAGE                COMMAND                  CREATED             STATUS              PORTS                    NAMES
84326b56f7eb        sha256serviceimage   "python3 ./SHA256Ser…"   26 seconds ago      Up 25 seconds       0.0.0.0:8080->8080/tcp   festive_moser
$ 

Test cases

(I) Post Requests

Positive Cases:

$  curl -X POST -H "Content-Type: application/json" -d '{"message": "sanjose"}' http://localhost:8080/messages
{
    "digest": "ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8"
}$ 

$ curl -iX POST -H "Content-Type: application/json" -d '{"message": "1234567"}' http://localhost:8080/messages
HTTP/1.1 200 OK
Content-Length: 84
Content-Type: text/html; charset=utf-8
Date: Sun, 08 Nov 2020 23:14:23 GMT
Server: waitress

{
    "digest": "8bb0cf6eb9b17d0f7d22b456f121257dc1254e1f01665370476383ea776df414"
}$ 

Negative Cases:

Post a message which already exists in datastore.

$ curl -iX POST -H "Content-Type: application/json" -d '{"message": "sanjose"}' http://localhost:8080/messages
HTTP/1.1 422 UNPROCESSABLE ENTITY
Content-Length: 94
Content-Type: text/html; charset=utf-8
Date: Sun, 08 Nov 2020 23:15:01 GMT
Server: waitress

{
    "error": "unable to process message, message already exists",
    "message": "sanjose"
}$ 


(II) Get requests

Positive Case:

$ curl -i http://localhost:8080/messages/ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8
HTTP/1.1 200 OK
Content-Length: 28
Content-Type: text/html; charset=utf-8
Date: Sun, 08 Nov 2020 23:15:35 GMT
Server: waitress

{
    "message": "sanjose"
}$ 

Negative Case

$ curl -i http://localhost:8080/messages/ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b4654
HTTP/1.1 404 NOT FOUND
Content-Length: 119
Content-Type: text/html; charset=utf-8
Date: Sun, 08 Nov 2020 23:15:59 GMT
Server: waitress

{
    "error": "unable to find message",
    "message_sha256": "ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b4654"
}$ 

(III) Delete Requests

Postive Case:

$ curl -iX DELETE http://localhost:8080/messages/ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8
HTTP/1.1 200 OK
Content-Length: 126
Content-Type: text/html; charset=utf-8
Date: Sun, 08 Nov 2020 23:16:28 GMT
Server: waitress

{
    "success": "Deleted message",
    "message_sha256": "ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8"
}$ 

Verify that its deleted:
$ curl -i http://localhost:8080/messages/ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8
HTTP/1.1 404 NOT FOUND
Content-Length: 131
Content-Type: text/html; charset=utf-8
Date: Sun, 08 Nov 2020 23:17:26 GMT
Server: waitress

{
    "error": "unable to find message",
    "message_sha256": "ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8"
}$ 


Negative Case:

$ curl -iX DELETE http://localhost:8080/messages/ce53c678303fa3e5678b3f614d1daeffc31e321378
HTTP/1.1 200 OK
Content-Length: 109
Content-Type: text/html; charset=utf-8
Date: Sun, 08 Nov 2020 21:34:05 GMT
Server: waitress

{
    "error": "unable to find message",
    "message_sha256": "ce53c678303fa3e5678b3f614d1daeffc31e321378"
}$ 


(IV) Get Metrics

Returns following metrics grouped per day
 - total requests count
 - average response time
 - total count of each type of request(POST, GET, DELETE)
 - total count of each status returned 
 - Details of every request

$ curl http://localhost:8080/metrics
{
    "Sunday, 08. November 2020": {
        "total_requests_count": 7,
        "all reqests": [
            {
                "time": "23:13:51",
                "source_ip": "172.17.0.1",
                "method": "POST",
                "status_code": "200",
                "status_message": "success",
                "url": "/messages",
                "response_time": "0.8 milliseconds"
            },
            {
                "time": "23:14:23",
                "source_ip": "172.17.0.1",
                "method": "POST",
                "status_code": "200",
                "status_message": "success",
                "url": "/messages",
                "response_time": "0.58 milliseconds"
            },
            {
                "time": "23:15:01",
                "source_ip": "172.17.0.1",
                "method": "POST",
                "status_code": "422",
                "status_message": "error",
                "url": "/messages",
                "response_time": "0.49 milliseconds"
            },
            {
                "time": "23:15:35",
                "source_ip": "172.17.0.1",
                "method": "GET",
                "status_code": "200",
                "status_message": "success",
                "url": "/messages/ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8",
                "response_time": "0.47 milliseconds"
            },
            {
                "time": "23:15:59",
                "source_ip": "172.17.0.1",
                "method": "GET",
                "status_code": "404",
                "status_message": "error",
                "url": "/messages/ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b4654",
                "response_time": "0.44 milliseconds"
            },
            {
                "time": "23:16:28",
                "source_ip": "172.17.0.1",
                "method": "DELETE",
                "status_code": "200",
                "status_message": "success",
                "url": "/messages/ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8",
                "response_time": "0.95 milliseconds"
            },
            {
                "time": "23:17:26",
                "source_ip": "172.17.0.1",
                "method": "GET",
                "status_code": "404",
                "status_message": "error",
                "url": "/messages/ce53c678303fa3e5678b3f614d1daeffc31e32137844b42b46546183bc8bb3d8",
                "response_time": "0.48 milliseconds"
            }
        ],
        "status_counts": {
            "200": 4,
            "422": 1,
            "404": 2
        },
        "method_counts": {
            "POST": 3,
            "GET": 3,
            "DELETE": 1
        },
        "Average Response Time": "0.6 milliseconds"
    }
}$ 


2. Running as a service on localhost.

Setup Instructions

Install python3 and pip3 on loca lhost.
Use pip3 to install module flask waitress

$ unzip SHA256Service.zip
Archive:  SHA256Service.zip
   creating: SHA256Service/
  inflating: SHA256Service/.DS_Store  
  inflating: __MACOSX/SHA256Service/._.DS_Store  
  inflating: SHA256Service/requirements.txt  
  inflating: SHA256Service/Dockerfile  
  inflating: SHA256Service/README.txt  
   creating: SHA256Service/src/
  inflating: SHA256Service/src/SHA256Server.py  
$ 

$ ls
__MACOSX	app		app.zip
MacBook-Pro:testing_app swayamprabhasoman$ cd SHA256Service/
$ python3 ./src/SHA256Server.py &
[1] 17009
$ Serving on http://0.0.0.0:8080

$ 

TestCases are same as that for Running in Docker Container Case.
