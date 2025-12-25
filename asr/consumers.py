import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ASRJob

@database_sync_to_async
def _check_owner(job_id: int, user, jwt_payload, application):
    job = ASRJob.objects.filter(id=job_id).first()
    if not job:
        return False
    if application:
        return job.application_id == application.id
    if user and getattr(user, "is_authenticated", False):
        return job.user_id == user.id
    if jwt_payload:
        sid = jwt_payload.get("sid")
        if sid and job.session_key == sid:
            return True
    return False

class JobConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope["url_route"]["kwargs"]["job_id"]
        self.group_name = f"job_{self.job_id}"

        user = self.scope.get("user") or AnonymousUser()
        jwt_payload = self.scope.get("token") or None
        application = self.scope.get("application")
        ok = await _check_owner(self.job_id, user, jwt_payload, application)
        if not ok:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def job_event(self, event):
        await self.send(text_data=json.dumps(event["data"]))
