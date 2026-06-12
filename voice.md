# REST

POST https://api.sarvam.ai/speech-to-text
Content-Type: multipart/form-data

## Speech to Text API

This API transcribes speech to text in multiple Indian languages and English. Supports transcription for interactive applications.

### Available Options:
- **REST API** (Current Endpoint): For quick responses under 30 seconds with immediate results
- **Batch API**: For longer audio files, [Follow This Documentation](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/speech-to-text/batch-api)
  - Supports diarization (speaker identification)

### Note:
- Pricing differs for REST and Batch APIs
- Diarization is only available in Batch API with separate pricing
- Please refer to [here](https://docs.sarvam.ai/api-reference-docs/pricing) for detailed pricing information

Reference: https://docs.sarvam.ai/api-reference-docs/speech-to-text/transcribe

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: ''
  version: 1.0.0
paths:
  /speech-to-text:
    post:
      operationId: transcribe
      summary: Speech to Text
      description: >-
        ## Speech to Text API


        This API transcribes speech to text in multiple Indian languages and
        English. Supports transcription for interactive applications.


        ### Available Options:

        - **REST API** (Current Endpoint): For quick responses under 30 seconds
        with immediate results

        - **Batch API**: For longer audio files, [Follow This
        Documentation](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/speech-to-text/batch-api)
          - Supports diarization (speaker identification)

        ### Note:

        - Pricing differs for REST and Batch APIs

        - Diarization is only available in Batch API with separate pricing

        - Please refer to
        [here](https://docs.sarvam.ai/api-reference-docs/pricing) for detailed
        pricing information
      tags:
        - subpackage_speechToText
      parameters:
        - name: api-subscription-key
          in: header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Sarvam_Model_API_SpeechToTextResponse'
        '400':
          description: Bad Request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Sarvam_Model_API_ErrorMessage'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Sarvam_Model_API_ErrorMessage'
        '422':
          description: Unprocessable Entity
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Sarvam_Model_API_ErrorMessage'
        '429':
          description: Quota Exceeded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Sarvam_Model_API_ErrorMessage'
        '500':
          description: Internal Server Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Sarvam_Model_API_ErrorMessage'
        '503':
          description: Service Overloaded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Sarvam_Model_API_ErrorMessage'
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                  description: >-
                    The audio file to transcribe. Supported formats include WAV,
                    MP3, AAC, AIFF, OGG, OPUS, FLAC, MP4/M4A, AMR, WMA, WebM,
                    and PCM formats. The API automatically detects most codec
                    formats, but for PCM files (pcm_s16le, pcm_l16, pcm_raw),
                    you must specify the input_audio_codec parameter. PCM files
                    are supported only at 16kHz sample rate.

                    The API works best with audio files sampled at 16kHz. If the
                    audio contains multiple channels, they will be merged into a
                    single channel.
                model:
                  $ref: '#/components/schemas/Sarvam_Model_API_SpeechToTextModel'
                  description: >-
                    Specifies the model to use for speech-to-text conversion.


                    - **saarika:v2.5** (default): Transcribes audio in the
                    spoken language.


                    - **saaras:v3**: State-of-the-art model with flexible output
                    formats. Supports multiple modes via the `mode` parameter:
                    transcribe, translate, verbatim, translit, codemix.
                mode:
                  oneOf:
                    - $ref: '#/components/schemas/Sarvam_Model_API_Mode'
                    - type: 'null'
                  default: transcribe
                  description: >-
                    Mode of operation. **Only applicable when using saaras:v3
                    model.**


                    Example audio: 'मेरा फोन नंबर है 9840950950'


                    - **transcribe** (default): Standard transcription in the
                    original language with proper formatting and number
                    normalization.
                      - Output: `मेरा फोन नंबर है 9840950950`

                    - **translate**: Translates speech from any supported Indic
                    language to English.
                      - Output: `My phone number is 9840950950`

                    - **verbatim**: Exact word-for-word transcription without
                    normalization, preserving filler words and spoken numbers
                    as-is.
                      - Output: `मेरा फोन नंबर है नौ आठ चार zero नौ पांच zero नौ पांच zero`

                    - **translit**: Romanization - Transliterates speech to
                    Latin/Roman script only.
                      - Output: `mera phone number hai 9840950950`

                    - **codemix**: Code-mixed text with English words in English
                    and Indic words in native script.
                      - Output: `मेरा phone number है 9840950950`
                language_code:
                  $ref: '#/components/schemas/Sarvam_Model_API_SpeechToTextLanguage'
                  description: >-
                    Specifies the language of the input audio in BCP-47 format.


                    **Note:** This parameter is optional for `saarika:v2.5`
                    model.


                    **Available Options:**

                    - `unknown`: Use when the language is not known; the API
                    will auto-detect.

                    - `hi-IN`: Hindi

                    - `bn-IN`: Bengali

                    - `kn-IN`: Kannada

                    - `ml-IN`: Malayalam

                    - `mr-IN`: Marathi

                    - `od-IN`: Odia

                    - `pa-IN`: Punjabi

                    - `ta-IN`: Tamil

                    - `te-IN`: Telugu

                    - `en-IN`: English

                    - `gu-IN`: Gujarati


                    **Additional Options (saaras:v3 only):**

                    - `as-IN`: Assamese

                    - `ur-IN`: Urdu

                    - `ne-IN`: Nepali

                    - `kok-IN`: Konkani

                    - `ks-IN`: Kashmiri

                    - `sd-IN`: Sindhi

                    - `sa-IN`: Sanskrit

                    - `sat-IN`: Santali

                    - `mni-IN`: Manipuri

                    - `brx-IN`: Bodo

                    - `mai-IN`: Maithili

                    - `doi-IN`: Dogri
                input_audio_codec:
                  $ref: '#/components/schemas/Sarvam_Model_API_InputAudioCodec'
                  description: >-
                    Input Audio codec/format of the input file. PCM files are
                    supported only at 16kHz sample rate.
              required:
                - file
servers:
  - url: https://api.sarvam.ai
    description: Production
components:
  schemas:
    Sarvam_Model_API_SpeechToTextModel:
      type: string
      enum:
        - saarika:v2.5
        - saaras:v3
      description: >-
        Model to be used for speech to text.


        - **saarika:v2.5** (default): Transcribes audio in the spoken language.


        - **saaras:v3**: State-of-the-art model with flexible output formats.
        Supports multiple modes via the `mode` parameter: transcribe, translate,
        verbatim, translit, codemix.
      title: Sarvam_Model_API_SpeechToTextModel
    Sarvam_Model_API_Mode:
      type: string
      enum:
        - transcribe
        - translate
        - verbatim
        - translit
        - codemix
      description: >-
        Mode of operation for saaras:v3 model.


        Example audio: 'मेरा फोन नंबर है 9840950950'


        - **transcribe** (default): Standard transcription in the original
        language with proper formatting and number normalization.
          - Output: `मेरा फोन नंबर है 9840950950`

        - **translate**: Translates speech from any supported Indic language to
        English.
          - Output: `My phone number is 9840950950`

        - **verbatim**: Exact word-for-word transcription without normalization,
        preserving filler words and spoken numbers as-is.
          - Output: `मेरा फोन नंबर है नौ आठ चार zero नौ पांच zero नौ पांच zero`

        - **translit**: Romanization - Transliterates speech to Latin/Roman
        script only.
          - Output: `mera phone number hai 9840950950`

        - **codemix**: Code-mixed text with English words in English and Indic
        words in native script.
          - Output: `मेरा phone number है 9840950950`
      title: Sarvam_Model_API_Mode
    Sarvam_Model_API_SpeechToTextLanguage:
      type: string
      enum:
        - unknown
        - hi-IN
        - bn-IN
        - kn-IN
        - ml-IN
        - mr-IN
        - od-IN
        - pa-IN
        - ta-IN
        - te-IN
        - en-IN
        - gu-IN
        - as-IN
        - ur-IN
        - ne-IN
        - kok-IN
        - ks-IN
        - sd-IN
        - sa-IN
        - sat-IN
        - mni-IN
        - brx-IN
        - mai-IN
        - doi-IN
      description: >-
        Languages supported for Speech-to-Text.


        **saarika:v2.5 supports (12 languages):** unknown, hi-IN, bn-IN, kn-IN,
        ml-IN, mr-IN, od-IN, pa-IN, ta-IN, te-IN, en-IN, gu-IN


        **saaras:v3 supports all 23 languages** including: as-IN, ur-IN, ne-IN,
        kok-IN, ks-IN, sd-IN, sa-IN, sat-IN, mni-IN, brx-IN, mai-IN, doi-IN
      title: Sarvam_Model_API_SpeechToTextLanguage
    Sarvam_Model_API_InputAudioCodec:
      type: string
      enum:
        - wav
        - x-wav
        - wave
        - mp3
        - mpeg
        - mpeg3
        - x-mp3
        - x-mpeg-3
        - aac
        - x-aac
        - aiff
        - x-aiff
        - ogg
        - opus
        - flac
        - x-flac
        - mp4
        - x-m4a
        - amr
        - x-ms-wma
        - webm
        - pcm_s16le
        - pcm_l16
        - pcm_raw
      description: >-
        Audio codec/format of the input file. Our API automatically detects all
        codec formats, but for PCM files specifically (pcm_s16le, pcm_l16,
        pcm_raw), you must pass this parameter. PCM files are supported only at
        16kHz sample rate.
      title: Sarvam_Model_API_InputAudioCodec
    Sarvam_Model_API_TimestampsModel:
      type: object
      properties:
        words:
          type: array
          items:
            type: string
          description: List of words in the transcript.
        start_time_seconds:
          type: array
          items:
            type: number
            format: double
          description: List of start times of words in seconds.
        end_time_seconds:
          type: array
          items:
            type: number
            format: double
          description: List of end times of words in seconds.
      required:
        - words
        - start_time_seconds
        - end_time_seconds
      title: Sarvam_Model_API_TimestampsModel
    Sarvam_Model_API_DiarizedEntry:
      type: object
      properties:
        transcript:
          type: string
          description: transcript of the segment of that audio
        start_time_seconds:
          type: number
          format: double
          description: Start time of the word in seconds.
        end_time_seconds:
          type: number
          format: double
          description: End time of the word in seconds.
        speaker_id:
          type: string
          description: Speaker ID for the word.
      required:
        - transcript
        - start_time_seconds
        - end_time_seconds
        - speaker_id
      title: Sarvam_Model_API_DiarizedEntry
    Sarvam_Model_API_DiarizedTranscript:
      type: object
      properties:
        entries:
          type: array
          items:
            $ref: '#/components/schemas/Sarvam_Model_API_DiarizedEntry'
          description: List of diarized transcript entries.
      required:
        - entries
      title: Sarvam_Model_API_DiarizedTranscript
    Sarvam_Model_API_SpeechToTextResponse:
      type: object
      properties:
        request_id:
          type:
            - string
            - 'null'
        transcript:
          type: string
          description: The transcribed text from the provided audio file.
        timestamps:
          oneOf:
            - $ref: '#/components/schemas/Sarvam_Model_API_TimestampsModel'
            - type: 'null'
          description: >-
            Contains timestamps for the transcribed text. This field is included
            only if with_timestamps is set to true
        diarized_transcript:
          oneOf:
            - $ref: '#/components/schemas/Sarvam_Model_API_DiarizedTranscript'
            - type: 'null'
          description: Diarized transcript of the provided speech
        language_code:
          type:
            - string
            - 'null'
          description: >-
            This will return the BCP-47 code of language spoken in the input. If
            multiple languages are detected, this will return language code of
            most predominant spoken language. If no language is detected, this
            will be null
        language_probability:
          type:
            - number
            - 'null'
          format: double
          description: >-
            Float value (0.0 to 1.0) indicating the probability of the detected
            language being correct. Higher values indicate higher confidence.


            **When it returns a value:**

            - When `language_code` is not provided in the request

            - When `language_code` is set to `unknown`


            **When it returns null:**

            - When a specific `language_code` is provided (language detection is
            skipped)


            The parameter is always present in the response.
      required:
        - request_id
        - transcript
        - language_code
      title: Sarvam_Model_API_SpeechToTextResponse
    Sarvam_Model_API_ErrorCode:
      type: string
      enum:
        - invalid_request_error
        - internal_server_error
        - unprocessable_entity_error
        - insufficient_quota_error
        - invalid_api_key_error
        - authentication_error
        - not_found_error
        - rate_limit_exceeded_error
      title: Sarvam_Model_API_ErrorCode
    Sarvam_Model_API_ErrorDetails:
      type: object
      properties:
        request_id:
          type:
            - string
            - 'null'
        message:
          type: string
          description: Message describing the error
        code:
          $ref: '#/components/schemas/Sarvam_Model_API_ErrorCode'
          description: >-
            Error code for the specific error that has occurred. Refer to the
            error code documentation for more details.
      required:
        - request_id
        - message
        - code
      title: Sarvam_Model_API_ErrorDetails
    Sarvam_Model_API_ErrorMessage:
      type: object
      properties:
        error:
          $ref: '#/components/schemas/Sarvam_Model_API_ErrorDetails'
          description: Error details
      required:
        - error
      title: Sarvam_Model_API_ErrorMessage
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: api-subscription-key

```

## Examples



**Request**

```json
{
  "file": "<file: interview_sample.wav>"
}
```

**Response**

```json
{
  "request_id": "20240615_1a2b3c4d-5678-90ab-cdef-1234567890ab",
  "transcript": "नमस्ते, आप कैसे हैं?",
  "language_code": "hi-IN",
  "timestamps": {
    "words": [
      "नमस्ते",
      "आप",
      "कैसे",
      "हैं?"
    ],
    "start_time_seconds": [
      0,
      0.5,
      1,
      1.5
    ],
    "end_time_seconds": [
      0.5,
      1,
      1.5,
      2
    ],
    "timestamps": {
      "end_time_seconds": [
        2
      ],
      "start_time_seconds": [
        0
      ],
      "words": [
        "नमस्ते, आप कैसे हैं?"
      ]
    }
  },
  "diarized_transcript": {
    "entries": [
      {
        "transcript": "नमस्ते, आप कैसे हैं?",
        "start_time_seconds": 0,
        "end_time_seconds": 2,
        "speaker_id": "speaker_1"
      }
    ]
  },
  "language_probability": 0.98
}
```

**SDK Code**

```typescript
import { SarvamAIClient } from "sarvamai";

async function main() {
    const client = new SarvamAIClient({
        apiSubscriptionKey: "YOUR_API_KEY_HERE",
    });
    await client.speechToText.transcribe(, {});
}
main();

```

```python
from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="YOUR_API_KEY_HERE",
)

client.speech_to_text.transcribe(
    file="example_file",
)

```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.sarvam.ai/speech-to-text"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"interview_sample.wav\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"mode\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language_code\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"input_audio_codec\"\r\n\r\n\r\n-----011000010111000001101001--\r\n")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("api-subscription-key", "<apiSubscriptionKey>")
	req.Header.Add("Content-Type", "multipart/form-data; boundary=---011000010111000001101001")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.sarvam.ai/speech-to-text")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["api-subscription-key"] = '<apiSubscriptionKey>'
request["Content-Type"] = 'multipart/form-data; boundary=---011000010111000001101001'
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"interview_sample.wav\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"mode\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language_code\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"input_audio_codec\"\r\n\r\n\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.post("https://api.sarvam.ai/speech-to-text")
  .header("api-subscription-key", "<apiSubscriptionKey>")
  .header("Content-Type", "multipart/form-data; boundary=---011000010111000001101001")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"interview_sample.wav\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"mode\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language_code\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"input_audio_codec\"\r\n\r\n\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.sarvam.ai/speech-to-text', [
  'multipart' => [
    [
        'name' => 'file',
        'filename' => 'interview_sample.wav',
        'contents' => null
    ]
  ]
  'headers' => [
    'api-subscription-key' => '<apiSubscriptionKey>',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.sarvam.ai/speech-to-text");
var request = new RestRequest(Method.POST);
request.AddHeader("api-subscription-key", "<apiSubscriptionKey>");
request.AddParameter("multipart/form-data; boundary=---011000010111000001101001", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"interview_sample.wav\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"mode\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language_code\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"input_audio_codec\"\r\n\r\n\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "api-subscription-key": "<apiSubscriptionKey>",
  "Content-Type": "multipart/form-data; boundary=---011000010111000001101001"
]
let parameters = [
  [
    "name": "file",
    "fileName": "interview_sample.wav"
  ],
  [
    "name": "model",
    "value": 
  ],
  [
    "name": "mode",
    "value": 
  ],
  [
    "name": "language_code",
    "value": 
  ],
  [
    "name": "input_audio_codec",
    "value": 
  ]
]

let boundary = "---011000010111000001101001"

var body = ""
var error: NSError? = nil
for param in parameters {
  let paramName = param["name"]!
  body += "--\(boundary)\r\n"
  body += "Content-Disposition:form-data; name=\"\(paramName)\""
  if let filename = param["fileName"] {
    let contentType = param["content-type"]!
    let fileContent = String(contentsOfFile: filename, encoding: String.Encoding.utf8)
    if (error != nil) {
      print(error as Any)
    }
    body += "; filename=\"\(filename)\"\r\n"
    body += "Content-Type: \(contentType)\r\n\r\n"
    body += fileContent
  } else if let paramValue = param["value"] {
    body += "\r\n\r\n\(paramValue)"
  }
}

let request = NSMutableURLRequest(url: NSURL(string: "https://api.sarvam.ai/speech-to-text")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```