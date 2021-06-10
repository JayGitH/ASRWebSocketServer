# ASR WebSocket Service

this a ASR system using  websockets to connection implement by python 3.7+

use the asyncio , aioredis and sanic (websockets)  to built this asr system 

support  concurrent client connection and concurrent multi-asr engine 

## 1.  Usage

make sure you python version is python 3.7 or above.

```bash
sanic websocket_server.app --host=0.0.0.0 --port=8000
# or
python websocket_server.py
```

### 1.1 Client

### 1.1.1 Connection establishment

```http
ws://localhost:8000/v1/asr?date=&appkey=&signature=
```



| parameter | description                               | example                                                |
| --------- | ----------------------------------------- | ------------------------------------------------------ |
| data      | timestamp                                 | 1623208573                                             |
| appkey    | authorization by appkey                   | 15954435476c6542ebcf1270cbba98e5  (random)             |
| signature | signature sign with hmac-sha256 algorithm | GvtMPND9hj9kHdOM357oab6UJH+ee+bFdJ/ss+QOVcs=  (random) |

### 1.1.2 Encrypt algorithm

signature_origin  string is here

```
host: yuntrans.vip
date: 1623208573
appkey: 15954435476c6542ebcf1270cbba98e5
GET /v1/asr  
```

encrypt: secret is the secret key that specific by yourself

```
signature_sha = hmac-sha256(signature_origin, Secret)
signature = Base64(signature_sha);
```

### 1.1.3  Send data



### 1.1.4 Transcription



## 2. Server



###  2.1 Architecture

![architecture](https://github.com/lovemefan/ASRWebSocketServer/raw/master/pic/Architecture.png)

this system will choose the specific asr handle by language code stored in redis

### 2.2 Extend ASR handle of custom  ASR engine 

* subscribe audio data from redis (or mq) vary from client to client identified by client id and manage those clients
* transcript from asr engine 
* publish transcription to redis identified by client id 

