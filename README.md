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

more detail in [document](https://450489712.gitbook.io/asr-websocket-service/)

Here is :

python [demo]([ASRWebSocketServer/asr_client.py at master · lovemefan/ASRWebSocketServer (github.com)](https://github.com/lovemefan/ASRWebSocketServer/blob/master/client/asr_client.py))

Java [demo]([ASRWebSocketServer/client/JavaDemo at master · lovemefan/ASRWebSocketServer (github.com)](https://github.com/lovemefan/ASRWebSocketServer/tree/master/client/JavaDemo))

### 1.1.1 Connection establishment

```http
ws://localhost:8000/v1/asr?date=1623399130&appkey=uopcp9EeuFJgBo66FwYw&signature=z8D75eBHU7iTuM7bIzx1YyeM9JxX230Gc87VL02Gpxk=
```



| parameter | description                               | example                                      |
| --------- | ----------------------------------------- | -------------------------------------------- |
| date      | timestamp                                 | 1623399130                                   |
| appkey    | authorization by appkey                   | uopcp9EeuFJgBo66FwYw                         |
| signature | signature sign with hmac-sha256 algorithm | z8D75eBHU7iTuM7bIzx1YyeM9JxX230Gc87VL02Gpxk= |
| Secret    | encrypt key                               | 2kCPFNALTgPbi9GIzOTCw1bPkvsjhwI9gsMKoRocKW8= |

### 1.1.2 Signature Encrypt algorithm

signature_origin  string is here

```
host: localhost:8000
date: 1623399130
appkey: uopcp9EeuFJgBo66FwYw
GET /v1/asr
```

encrypt: secret is the secret key that specific by yourself

```
signature_sha = hmac-sha256(signature_origin, Secret)
signature = Base64(signature_sha);
```



### 1.1.3  Send data

The  format of data must be json,like:

```json
{
"language_code": "zh",
"audio_format": "wav/16000",
"status": "partial",
"data": "+Ofv7MvxT/Mq9u35gvyUA1cQexiSGQISexEJGAUaohbDET8KnQN6AQn+S/iz9lL47PNL78ry0Pke/QD+yf6NAGwFXgpRCnAHQwYfBckCev3t+Lj2pPJ47ZDnpOVG5uLkiuP74hrkT9+/oV+gAD/Q8CGLUZhhlqF+8F3PQF8K7uffDA+H4AlAZdDb0PIAx7DOcRXxGgDsgPQA4sBSP7tPYa8OjuD/S49yL96wUzCQoHsQU="
}
```

 

| parameter     | description                                                  | example   |
| ------------- | ------------------------------------------------------------ | --------- |
| language_code | language code                                                | zh        |
| audio_format  | audio format and bit rate                                    | wav/16000 |
| status        | [start, partial, end]   send the first data set the status `start`,last data set status `end` else status is `partial` | start     |
| data          | the base64 code of 1280 byte audio data                      |           |

we need send the json data to the server 

## 2. Server



###  2.1 Architecture

![architecture](https://github.com/lovemefan/ASRWebSocketServer/raw/master/pic/Architecture.png)

this system will choose the specific asr handle by language code stored in redis

### 2.2 Extend ASR handle of custom  ASR engine 

* subscribe audio data from redis (or mq) vary from client to client identified by client id and manage those clients
* transcript from asr engine 
* publish transcription to redis identified by client id 
