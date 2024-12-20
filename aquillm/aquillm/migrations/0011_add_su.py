from django.db import migrations
import os

class Migration(migrations.Migration):

    dependencies = [("aquillm", "0010_alter_llmconversation_system_prompt_wsconversation")]

    def generate_superuser(apps, schema_editor):
        if os.environ.get('DJANGO_DEBUG'):
            User = apps.get_model('auth', 'User')
            superuser = User.objects.create_superuser(
                username='dev',
                email='dev@example.com',
                password='rickbailey')

            superuser.save()


    operations = [
        migrations.RunPython(generate_superuser),
    ]