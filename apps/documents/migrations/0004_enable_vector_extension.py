from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0003_documentchunk"),
    ]

    operations = [
        VectorExtension(),
    ]