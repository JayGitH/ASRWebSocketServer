/**
 *
 * 实时转写调用demo
 * 此demo只是一个简单的调用示例
 * 
 */
 
// 音频转码worker
let recorderWorker = new Worker('./transformpcm.worker.js')
// 记录处理的缓存音频
let buffer = []
let AudioContext = window.AudioContext || window.webkitAudioContext
let notSupportTip = '请试用chrome浏览器且域名为localhost或127.0.0.1测试'
navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia

recorderWorker.onmessage = function (e) {
  buffer.push(...e.data.buffer)
}

class IatRecorder {
  constructor (config) {
    this.config = config
    this.state = 'start'

    this.appkey = 'uopcp9EeuFJgBo66FwYw' 
    this.secret = '2kCPFNALTgPbi9GIzOTCw1bPkvsjhwI9gsMKoRocKW8='
  }

  start () {
    this.stop()
    if (navigator.getUserMedia && AudioContext) {
      this.state = 'start'
      if (!this.recorder) {
        var context = new AudioContext()
        this.context = context
        this.recorder =context.createScriptProcessor(0, 1, 1)

        var getMediaSuccess = (stream) => {
          var mediaStream = this.context.createMediaStreamSource(stream)
          this.mediaStream = mediaStream
          this.recorder.onaudioprocess = (e) => {
            this.sendData(e.inputBuffer.getChannelData(0))
          }
          this.connectWebsocket()
        }
        var getMediaFail = (e) => {
          this.recorder = null
          this.mediaStream = null
          this.context = null
          console.log(e)
          console.log('请求麦克风失败')
        }
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          navigator.mediaDevices.getUserMedia({
            audio: true,
            video: false
          }).then((stream) => {
            getMediaSuccess(stream)
          }).catch((e) => {
            getMediaFail(e)
          })
        } else {
          navigator.getUserMedia({
            audio: true,
            video: false
          }, (stream) => {
            getMediaSuccess(stream)
          }, function (e) {
            getMediaFail(e)
          })
        }
      } else {
        this.connectWebsocket()
      }
    } else {
      var isChrome = navigator.userAgent.toLowerCase().match(/chrome/)
      alert(notSupportTip)
    }
  }
    
  stop () {
    this.state = 'end'
    try {      
      this.mediaStream.disconnect(this.recorder)
      this.recorder.disconnect()
    } catch (e) {}
  }
  
  sendData (buffer) {
    recorderWorker.postMessage({
      command: 'transform',
      buffer: buffer
    })
  }
  // 生成握手参数
  getHandShakeParams(host, port, path) {
    var appkey = this.appkey
    var secretKey = this.secret
    var ts = Math.floor(new Date().getTime()/1000);
    var signatureOrigin = "host: " + host + ":" + port + "\n" +
    "date: " + ts + "\n" +
    "appkey: " + appkey + "\n" +
    "GET " + path;
    console.log(signatureOrigin)
    var signatureSha = CryptoJS.HmacSHA256(signatureOrigin, secretKey)
    var signature = CryptoJS.enc.Base64.stringify(signatureSha)
    signature = encodeURIComponent(signature)
    return "?appkey=" + appkey + "&date=" + ts + "&signature=" +signature;
  }

  connectWebsocket () {
    var url = 'ws://yuntrans.vip:8000/v1/asr'
    var urlParam = this.getHandShakeParams('yuntrans.vip', '8000', '/v1/asr')
    
    url = `${url}${urlParam}`
    console.log(url)
    if ('WebSocket' in window) {
      this.ws = new WebSocket(url)
      console.log(this.ws)
    } else if ('MozWebSocket' in window) {
      this.ws = new MozWebSocket(url)
    } else {
      alert(notSupportTip)
      return null
    }
    this.ws.onopen = (e) => {
      this.mediaStream.connect(this.recorder)
      this.recorder.connect(this.context.destination)

      this.ws.send("{\n" +
      "\"language_code\": \"zh\",\n" +
      "\"audio_format\": \"wav/16000\",\n" +
      "\"status\": \"start\",\n" +
      "\"data\": \"\"\n" +
      "}")

      setTimeout(() => {
        this.wsOpened(e)
      }, 500)
      this.config.onStart && this.config.onStart(e)
    }
    this.ws.onmessage = (e) => {
      // this.config.onMessage && this.config.onMessage(e)
      this.wsOnMessage(e)
    }
    this.ws.onerror = (e) => {
      this.stop()
      console.log("关闭连接ws.onerror");
      this.config.onError && this.config.onError(e)
    }
    this.ws.onclose = (e) => {
      this.stop()
      console.log("关闭连接ws.onclose");
      $('.start-button').attr('disabled', false);
      this.config.onClose && this.config.onClose(e)
    }
  }
  
  wsOpened () {
    if (this.ws.readyState !== 1) {
      return
    }
    
 
    let data = "{\n" +
    "\"language_code\": \"zh\",\n" +
    "\"audio_format\": \"wav/16000\",\n" +
    "\"status\": \"start\",\n" +
    "\"data\": \"\"\n" +
    "}";

    this.ws.send(data)
    this.handlerInterval = setInterval(() => {
      // websocket未连接
      if (this.ws.readyState !== 1) {
        clearInterval(this.handlerInterval)
        return
      }
      if (buffer.length === 0) {
        if (this.state === 'end') {
          this.ws.send("{\n" +
        "\"language_code\": \"zh\",\n" +
        "\"audio_format\": \"wav/16000\",\n" +
        "\"status\": \"end\",\n" +
        "\"data\": \"\"\n" +
        "}")

        
          console.log("发送结束标识");
          clearInterval(this.handlerInterval)
          return false
        }
        
      }
      var audioData = buffer.splice(0, 1280)
      if(audioData.length > 0){
        let data = "{\n" +
        "\"language_code\": \"zh\",\n" +
        "\"audio_format\": \"wav/16000\",\n" +
        "\"status\": \"partial\",\n" +
        "\"data\": \"" + this.ArrayBufferToBase64(audioData) + "\"\n" +
        "}";
        
        this.ws.send(data)
      }
    }, 40)
  }

  wsOnMessage(e){
    let jsonData = JSON.parse(e.data)
    console.log(jsonData)
    if (jsonData.data.status == "start") {
      // 握手成功
      console.log("握手成功");
    } else if (jsonData.data.status == "partial") {
        // 转写结果
        if(this.config.onMessage && typeof this.config.onMessage == 'function'){
          this.config.onMessage(jsonData.data.result, jsonData.data.status)
        }
    } else if (jsonData.data.status == "final") {
      // 转写结果
      if(this.config.onMessage && typeof this.config.onMessage == 'function'){
        this.config.onMessage(jsonData.data.result, jsonData.data.status)
      }
    } else if (jsonData.data.status == "error") {
        // 连接发生错误
        console.log("出错了:",jsonData);
    }
  }
  

  ArrayBufferToBase64 (buffer) {
    var binary = ''
    var bytes = new Uint8Array(buffer)
    var len = bytes.byteLength
    for (var i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return window.btoa(binary)
  }
}

class IatTaste {
  constructor () {
    var iatRecorder = new IatRecorder({
      onClose: () => {
        this.stop()
        this.reset()
      },
      onError: (data) => {
        this.stop()
        this.reset()
        alert('WebSocket连接失败')
      },
      onMessage: (message, status) =>{
        this.setResult(message, status)
      },
      onStart: () => {
        $('hr').addClass('hr')
        var dialect = $('.dialect-select').find('option:selected').text()
        $('.taste-content').css('display', 'none')
        $('.start-taste').addClass('flex-display-1')
        $('.dialect-select').css('display', 'none')
        $('.start-button').text('结束转写')
        $('.time-box').addClass('flex-display-1')
        $('.dialect').text(dialect).css('display', 'inline-block')
        this.counterDown($('.used-time'))
      }
    })
    this.iatRecorder = iatRecorder
    this.counterDownDOM = $('.used-time')
    this.counterDownTime = 0

    this.text = {
      start: '开始转写',
      stop: '结束转写'
    }
    this.resultText = ''
  }

  start () {
    this.iatRecorder.start()
  }

  stop () {
    $('hr').removeClass('hr')
    this.iatRecorder.stop()
  }

  reset () {
    this.counterDownTime = 0
    clearTimeout(this.counterDownTimeout)
    buffer = []
    $('.time-box').removeClass('flex-display-1').css('display', 'none')
    $('.start-button').text(this.text.start)
    $('.dialect').css('display', 'none')
    $('.dialect-select').css('display', 'inline-block')
    $('.taste-button').css('background', '#0b99ff')
  }

  init () {
    let self = this
    //开始
    $('#taste_button').click(function () {
      if (navigator.getUserMedia && AudioContext && recorderWorker) {
        self.start()
      } else {
        alert(notSupportTip)
      }
    })
    //结束
    $('#start-button').click(function () {
      if ($(this).text() === self.text.start && !$(this).prop('disabled')) {
        $('#result_output').text('')
        self.resultText = ''
        self.start()
        //console.log("按钮非禁用状态，正常启动" + $(this).prop('disabled'))
      } else {
        //$('.taste-content').css('display', 'none')
        $('#start-button').attr('disabled', true);
        self.stop()
        //reset
        this.counterDownTime = 0
        clearTimeout(this.counterDownTimeout)
        buffer = []
        $('#time-box').removeClass('flex-display-1').css('display', 'none')
        $('#start-button').text('转写停止')
        $('.dialect').css('display', 'none')
        $('#taste_button').css('background', '#8E8E8E')
        $('.dialect-select').css('display', 'inline-block')
        
        //console.log("按钮非禁用状态，正常停止" + $(this).prop('disabled'))
      }
    })
  }
  setResult (data, status) {
    console.log(data, status)
    var currentText = $('#result_output').html()
    if (status == 'final') {
        this.resultText += data
        $('#result_output').html(this.resultText)
    }else{
      if (currentText.length == 0) {
        $('#result_output').html(data)
        this.resultText = data
      } else {
        $('#result_output').html(this.resultText + data)
      }
    }
    
    var ele = document.getElementById('result_output');
    ele.scrollTop = ele.scrollHeight;
  }

  counterDown () {
    /*//计时5分钟
    if (this.counterDownTime === 300) {
      this.counterDownDOM.text('05: 00')
      this.stop()
    } else if (this.counterDownTime > 300) {
      this.reset()
      return false
    } else */ 
    if (this.counterDownTime >= 0 && this.counterDownTime < 10) {
      this.counterDownDOM.text('00: 0' + this.counterDownTime)
    } else if (this.counterDownTime >= 10 && this.counterDownTime < 60) {
      this.counterDownDOM.text('00: ' + this.counterDownTime)
    } else if (this.counterDownTime%60 >=0 && this.counterDownTime%60 < 10) {
      this.counterDownDOM.text('0' + parseInt(this.counterDownTime/60) + ': 0' + this.counterDownTime%60)
    } else {
      this.counterDownDOM.text('0' + parseInt(this.counterDownTime/60) + ': ' + this.counterDownTime%60)
    }
    this.counterDownTime++
    this.counterDownTimeout = setTimeout(() => {
      this.counterDown()
    }, 1000)
  }
}
var iatTaste = new IatTaste()
iatTaste.init()