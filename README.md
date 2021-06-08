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



## 2. Architecture

![architecture](https://github.com/lovemefan/ASRWebSocketServer/raw/master/pic/Architecture.png)

