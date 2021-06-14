/**
 * 此demo只是一个简单的调用示例
 * @Time  : 2021/6/13 11:56
 * @Author : lovemefan
 * @Email : lovemefan@outlook.com
 *
 */

import java.io.RandomAccessFile;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URLEncoder;
import java.nio.ByteBuffer;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;
import java.util.Objects;
import java.util.concurrent.CountDownLatch;

import org.apache.commons.codec.binary.Base64;
import org.java_websocket.WebSocket.READYSTATE;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.drafts.Draft;
import org.java_websocket.handshake.ServerHandshake;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import pojo.AudioBody;
import util.EncryptUtil;


import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;



public class Client {

    // appid
    private String APPKEY = "";

    // appkey对应的secret_key
    private String SECRET_KEY = "";

    // 请求地址
    private String HOST = "";



    private static final SimpleDateFormat sdf = new SimpleDateFormat("yyy-MM-dd HH:mm:ss.SSS");
    // 音频文件路径
    private String AUDIO_PATH = "./resource/test_1.pcm";

    // 每次发送的数据大小 1280 字节
    public static final int CHUNCKED_SIZE = 1280;

    public Client(String APPKEY, String SECRET_KEY) {
        this.APPKEY = APPKEY;
        this.SECRET_KEY = SECRET_KEY;
    }

    /**
     * 生成握手参数
     * @return  signature
     */
    public String getHandShakeParams() throws URISyntaxException {
        String ts = System.currentTimeMillis()/1000 + "";
        URI uri = new URI(this.HOST);
        String domain = uri.getHost();
        String path = uri.getPath();
        int port = uri.getPort();

        String signatureOrigin = "host: " + domain + ":" + port + "\n" +
                "date: " + ts + "\n" +
                "appkey: " + this.APPKEY + "\n" +
                "GET " + path;

        System.out.println(signatureOrigin);
        String signature = "";
        try {
            signature = EncryptUtil.HmacSHA256Encrypt(signatureOrigin, this.SECRET_KEY);
            return "?appkey=" + this.APPKEY + "&date=" + ts + "&signature=" + URLEncoder.encode(signature, "UTF-8");
        } catch (Exception e) {
            e.printStackTrace();
        }

        return "";
    }

    public String createUrl(String host) throws URISyntaxException {
        this.HOST = host;
        return host + this.getHandShakeParams();
    }

    public static void send(WebSocketClient client, byte[] bytes) {
        if (client.isClosed()) {
            throw new RuntimeException("client connect closed!");
        }

        client.send(bytes);
    }

    public static String getCurrentTimeStr() {
        return sdf.format(new Date());
    }

    public static class MyWebSocketClient extends WebSocketClient {

        private CountDownLatch handshakeSuccess;
        private CountDownLatch connectClose;

        public MyWebSocketClient(URI serverUri, CountDownLatch handshakeSuccess, CountDownLatch connectClose) {
            super(serverUri);
            this.handshakeSuccess = handshakeSuccess;
            this.connectClose = connectClose;
            if(serverUri.toString().contains("wss")){
                trustAllHosts(this);
            }
        }

        @Override
        public void onOpen(ServerHandshake handshake) {
            System.out.println(getCurrentTimeStr() + "\t连接建立成功！");
            handshakeSuccess.countDown();
        }

        @Override
        public void onMessage(String msg) {
            JSONObject msgObj = JSON.parseObject(msg);
            System.out.println(msgObj);
            String statusCode  = msgObj.getString("code");
            System.out.println(statusCode);
            if ("200".equals(statusCode)) {
                String status = msgObj.getJSONObject("data").getString("status");
                if (Objects.equals("start", status)) {
                    // 握手成功
                    System.out.println(getCurrentTimeStr() + "\t握手成功！sid: " + msgObj.getString("sid"));

                } else if (Objects.equals("partial", status)) {
                    // 转写结果
                    System.out.println(getCurrentTimeStr() + "\tresult: " + getContent(msgObj.getString("data")));
                } else if (Objects.equals("final", status)) {
                    // 转写的最后的结果
                    System.out.println(getCurrentTimeStr() + "\tresult: " + getContent(msgObj.getString("data")));
                } else if (Objects.equals("error", status)) {
                    // 连接发生错误
                    System.out.println("Error: " + msg);
                    System.exit(0);
                }
            } else {
                // 建立连接失败
                System.out.println(msgObj);
            }


        }

        @Override
        public void onError(Exception e) {
            System.out.println(getCurrentTimeStr() + "\t连接发生错误：" + e.getMessage() + ", " + new Date());
            e.printStackTrace();
            System.exit(0);
        }

        @Override
        public void onClose(int arg0, String arg1, boolean arg2) {
            System.out.println(getCurrentTimeStr() + "\t链接关闭");
            connectClose.countDown();
        }

        @Override
        public void onMessage(ByteBuffer bytes) {
            try {
                System.out.println(getCurrentTimeStr() + "\t服务端返回：" + new String(bytes.array(), "UTF-8"));
            } catch (UnsupportedEncodingException e) {
                e.printStackTrace();
            }
        }

        public void trustAllHosts(MyWebSocketClient appClient) {
            System.out.println("wss");
            TrustManager[] trustAllCerts = new TrustManager[]{new X509TrustManager() {
                @Override
                public java.security.cert.X509Certificate[] getAcceptedIssuers() {
                    return new java.security.cert.X509Certificate[]{};
                }

                @Override
                public void checkClientTrusted(X509Certificate[] arg0, String arg1) throws CertificateException {
                    // TODO Auto-generated method stub

                }

                @Override
                public void checkServerTrusted(X509Certificate[] arg0, String arg1) throws CertificateException {
                    // TODO Auto-generated method stub

                }
            }};

            try {
                SSLContext sc = SSLContext.getInstance("TLS");
                sc.init(null, trustAllCerts, new java.security.SecureRandom());
                appClient.setSocket(sc.getSocketFactory().createSocket());
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    // 把转写结果解析为句子
    public static String getContent(String message) {
        StringBuffer resultBuilder = new StringBuffer();
        try {
            JSONObject messageObj = JSON.parseObject(message);
            JSONObject cn = messageObj.getJSONObject("cn");
            JSONObject st = cn.getJSONObject("st");
            JSONArray rtArr = st.getJSONArray("rt");
            for (int i = 0; i < rtArr.size(); i++) {
                JSONObject rtArrObj = rtArr.getJSONObject(i);
                JSONArray wsArr = rtArrObj.getJSONArray("ws");
                for (int j = 0; j < wsArr.size(); j++) {
                    JSONObject wsArrObj = wsArr.getJSONObject(j);
                    JSONArray cwArr = wsArrObj.getJSONArray("cw");
                    for (int k = 0; k < cwArr.size(); k++) {
                        JSONObject cwArrObj = cwArr.getJSONObject(k);
                        String wStr = cwArrObj.getString("w");
                        resultBuilder.append(wStr);
                    }
                }
            }
        } catch (Exception e) {
            return message;
        }

        return resultBuilder.toString();
    }
}


class TestWebScoket {
    public static void main(String[] args) throws Exception {

        String host = "ws://localhost:8000/v1/asr";
        Client client = new Client("uopcp9EeuFJgBo66FwYw", "2kCPFNALTgPbi9GIzOTCw1bPkvsjhwI9gsMKoRocKW8=");
        String audioPath = "src/test_1.pcm";
        while (true) {
            System.out.println(client.createUrl(host));
            URI url = new URI(client.createUrl(host));
            CountDownLatch handshakeSuccess = new CountDownLatch(1);
            CountDownLatch connectClose = new CountDownLatch(1);
            Client.MyWebSocketClient wsClient = new Client.MyWebSocketClient(url, handshakeSuccess, connectClose);

            wsClient.connect();


            System.out.println(client.getCurrentTimeStr() + "\t连接中");

            // 等待握手成功
            handshakeSuccess.await();

            System.out.println(client.getCurrentTimeStr()  + " 开始发送音频数据");
            // 发送音频
            byte[] bytes = new byte[client.CHUNCKED_SIZE];
            try (RandomAccessFile raf = new RandomAccessFile(audioPath, "r")) {
                int len = -1;
                long lastTs = 0;
                String status = "start";
                while ((len = raf.read(bytes)) != -1) {
                    if (len < client.CHUNCKED_SIZE) {
                        client.send(wsClient, bytes = Arrays.copyOfRange(bytes, 0, len));
                        break;
                    }

                    long curTs = System.currentTimeMillis();
                    if (lastTs == 0) {
                        lastTs = System.currentTimeMillis();
                    } else {
                        long s = curTs - lastTs;
                        if (s < 40) {
                            System.out.println("error time interval: " + s + " ms");
                        }
                    }

                    AudioBody body = new AudioBody("zh", "wav/16000", status, new String(Base64.encodeBase64(bytes)));
                    System.out.println(body);
                    client.send(wsClient, body.getBytes());
                    // 每隔40毫秒发送一次数据
                    Thread.sleep(40);
                    status = "partial";
                }

                // 发送结束标识
                AudioBody body = new AudioBody("zh", "wav/16000", "end", "");
                System.out.println(body);
                client.send(wsClient, body.getBytes());
                System.out.println(client.getCurrentTimeStr() + "\t发送结束完成");
            } catch (Exception e) {
                e.printStackTrace();
            }

            // 等待连接关闭
            connectClose.await();
            break;
        }
    }
}