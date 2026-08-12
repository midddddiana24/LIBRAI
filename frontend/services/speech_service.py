from services.api_client import ApiResult, api_client


class SpeechService:
    def transcribe(self, file_path: str) -> ApiResult:
        return api_client.upload_file("/speech/transcribe", file_path, field_name="audio")


speech_service = SpeechService()
