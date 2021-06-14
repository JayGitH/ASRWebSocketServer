# 客户端使用API

Python [Demo](https://github.com/lovemefan/ASRWebSocketServer/blob/master/client/asr_client.py)

Java [Demo](https://github.com/lovemefan/ASRWebSocketServer/tree/master/client/JavaDemo)

{% api-method method="get" host="ws://localhost:8000" path="/v1/asr" %}
{% api-method-summary %}
ASR
{% endapi-method-summary %}

{% api-method-description %}

{% endapi-method-description %}

{% api-method-spec %}
{% api-method-request %}
{% api-method-query-parameters %}
{% api-method-parameter name="signature" type="string" required=true %}
加密签名
{% endapi-method-parameter %}

{% api-method-parameter name="date" type="integer" required=true %}
10 位的时间戳
{% endapi-method-parameter %}

{% api-method-parameter name="appkey" type="string" required=true %}
app key
{% endapi-method-parameter %}
{% endapi-method-query-parameters %}
{% endapi-method-request %}

{% api-method-response %}
{% api-method-response-example httpCode=200 %}
{% api-method-response-example-description %}
完成握手，通过身份验证且数据发送正确
{% endapi-method-response-example-description %}

```
{
    "code": 200, 
    "message": "SUCCESS", 
    "data": {
        "task_id": 1404335017064276000, 
        "speech_id": "yuntrans@137d334255022000", 
        "status": "start", 
        "result": ""
    }
}
```
{% endapi-method-response-example %}

{% api-method-response-example httpCode=401 %}
{% api-method-response-example-description %}
授权失败或者当前链接已失效，需要重新握手连接
{% endapi-method-response-example-description %}

```
{"code": 401, "message": "Unauthorized or Timeout", "data": ""}
```
{% endapi-method-response-example %}

{% api-method-response-example httpCode=403 %}
{% api-method-response-example-description %}
发送的数据不满足json的格式  
websocket 被服务器中中断
{% endapi-method-response-example-description %}

```
{"code": 401, "message": "The data must be json format", "data": ""}


{"code": 401, "message": "The websocket disconnect", "data": ""}

```
{% endapi-method-response-example %}

{% api-method-response-example httpCode=408 %}
{% api-method-response-example-description %}
长时间未发送数据被服务端关闭连接
{% endapi-method-response-example-description %}

```
{"code": 408, "message": "Connection Timeout", "data": ""}
```
{% endapi-method-response-example %}
{% endapi-method-response %}
{% endapi-method-spec %}
{% endapi-method %}

## 1. 签名

签名需要由app key和对应的secret 签名的伪代码如下，具体可以去查看 python和java实现的demo 

```python
signature_origin = """host: localhost:8000
date: 1623399130
appkey: uopcp9EeuFJgBo66FwYw
GET /v1/asr"""

signature_sha = hmac-sha256(signature_origin, Secret)
signature = Base64(signature_sha);
```

## 2. 发送数据

```python
{
"language_code": "zh",
"audio_format": "wav/16000",
"status": "partial",
"data": "+Ofv7MvxT/Mq9u35gvyUA1cQexiSGQISexEJGAUaohbDET8KnQN6AQn+S/iz9lL47PNL78ry0Pke/QD+yf6NAGwFXgpRCnAHQwYfBckCev3t+Lj2pPJ47ZDnpOVG5uLkiuP74hrkT9+/oV+gAD/Q8CGLUZhhlqF+8F3PQF8K7uffDA+H4AlAZdDb0PIAx7DOcRXxGgDsgPQA4sBSP7tPYa8OjuD/S49yL96wUzCQoHsQU="
}
```

{% hint style="danger" %}
发送的格式必须是json的格式
{% endhint %}



| 参数 | 描述 | 值 |
| :--- | :--- | :--- |
| language\_code | language code | zh |
| audio\_format | 语音的格式和比特率，目前强制要求为wav格式，16000比特率，单通道音频 | wav/16000 |
| status | 有三种状态\[start, partial, end\]，第一次发送数据是status是start，最后一次接受status是end，中间数据status为partial | start |
| data | 语音二进制数据的base64编码，一次通常取1280字节的数据 | +ofv7MvxT... |

## 3. 返回数据

异常返回请看上面Response

以下为正常返回数据，

```python
# 状态为start 没有转译文本
{
    "code": 200, 
    "data": {
        "result": "", 
        "task_id": 1404358647252918300, 
        "speech_id": "yuntrans@137d48c03a022000", 
        "status": "start"
    }, 
    "task_id": 1404358647252918300, 
    "message": "SUCCESS"
}
# 状态为partial 为每一句话的中间结果
{
    "code": 200, 
    "data": {
        "result": "当前明月光疑", 
        "task_id": 1404358647252918300, 
        "speech_id": "yuntrans@137d48c2bbc22000", 
        "status": "partial"
    }, 
    "task_id": 1404358647252918300, 
    "message": "SUCCESS"
}
# 状态为final 为每一句话最终结果
{
    "code": 200, 
    "data": {
        "result": "当前明月光，疑是地上霜，举头望明月，低头思故乡。", 
        "task_id": 1404358647252918300, 
        "speech_id": "yuntrans@137d48c589822000", 
        "status": "final"
    }, 
    "task_id": 1404358647252918300, 
    "message": "SUCCESS"
}
```

| 参数 | 描述 |
| :--- | :--- |
| code | 状态码 |
| data | 返回数据，json格式 |
| task\_id | 唯一任务id，每个连接是同一个任务id |
| message | 提示消息 |
| data.result | 识别结果 |
| data.task\_id | 同上 |
| data.speech\_id | 每个识别结果唯一id |
| data.status | 转写结果状态，start 为开始，无结果。partial为中间结果，final为每句话的最终结果。没个音频有多句话，有多个final |
|  |  |

