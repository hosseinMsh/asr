from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from asr.models import UserProfile, Profile

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
    Profile.objects.get_or_create(user=instance)
