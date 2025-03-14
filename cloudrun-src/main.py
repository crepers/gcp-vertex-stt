import asyncio
import websockets
from google.cloud import speech

async def transcribe_streaming(websocket, path):
    """WebSocket을 통해 오디오를 수신하고 Vertex AI Speech-to-Text로 변환합니다."""

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR",
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    async def request_generator():
        try:
            while True:
                audio_data = await websocket.recv()
                yield speech.StreamingRecognizeRequest(audio_content=audio_data)
        except websockets.exceptions.ConnectionClosedOK:
            pass

    requests = request_generator()
    responses = client.streaming_recognize(config=streaming_config, requests=requests)

    try:
        for response in responses:
            for result in response.results:
                alternative = result.alternatives[0]
                transcript = alternative.transcript
                if result.is_final:
                    await websocket.send(f"Final: {transcript}")
                else:
                    await websocket.send(f"Interim: {transcript}")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    """WebSocket 서버를 시작합니다."""
    async with websockets.serve(transcribe_streaming, "0.0.0.0", 8080):
        await asyncio.Future()  # 서버를 계속 실행합니다.

if __name__ == "__main__":
    asyncio.run(main())