package pojo;

public class AudioBody {
    private String languageCode;
    private String audioFormat;
    private String status;
    private String data;

    public AudioBody(String languageCode, String audioFormat, String status, String data) {
        this.languageCode = languageCode;
        this.audioFormat = audioFormat;
        this.status = status;
        this.data = data;
    }

    public String getLanguageCode() {
        return languageCode;
    }

    public void setLanguageCode(String languageCode) {
        this.languageCode = languageCode;
    }

    public String getAudioFormat() {
        return audioFormat;
    }

    public void setAudioFormat(String audioFormat) {
        this.audioFormat = audioFormat;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getData() {
        return data;
    }

    public void setData(String data) {
        this.data = data;
    }

    @Override
    public String toString() {
        return "{" +
                "\"language_code\": \"" + languageCode + "\",\n" +
                "\"audio_format\": \"" + audioFormat + "\",\n" +
                "\"status\": \"" + status + "\",\n" +
                "\"data\": \"" + data + "\"\n" +
                '}';
    }

    public byte[] getBytes() {
        return this.toString().getBytes();
    }
}
