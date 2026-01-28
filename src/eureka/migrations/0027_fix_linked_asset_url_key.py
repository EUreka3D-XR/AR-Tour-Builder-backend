from django.db import migrations


def fix_linked_asset_content_url(apps, schema_editor):
    """
    Fix linked_asset data where 'content_url' was mistakenly used instead of 'url'.
    """
    POIAsset = apps.get_model('eureka', 'POIAsset')
    for poi_asset in POIAsset.objects.exclude(linked_asset__isnull=True):
        if poi_asset.linked_asset and 'locales' in poi_asset.linked_asset:
            updated = False
            for locale, data in poi_asset.linked_asset['locales'].items():
                if isinstance(data, dict) and 'content_url' in data and 'url' not in data:
                    data['url'] = data.pop('content_url')
                    updated = True
            if updated:
                poi_asset.save(update_fields=['linked_asset'])


def reverse_fix(apps, schema_editor):
    """
    Reverse the fix (convert 'url' back to 'content_url').
    """
    POIAsset = apps.get_model('eureka', 'POIAsset')
    for poi_asset in POIAsset.objects.exclude(linked_asset__isnull=True):
        if poi_asset.linked_asset and 'locales' in poi_asset.linked_asset:
            updated = False
            for locale, data in poi_asset.linked_asset['locales'].items():
                if isinstance(data, dict) and 'url' in data and 'content_url' not in data:
                    data['content_url'] = data.pop('url')
                    updated = True
            if updated:
                poi_asset.save(update_fields=['linked_asset'])


class Migration(migrations.Migration):
    dependencies = [
        ('eureka', '0026_change_poi_asset_source_asset_on_delete_to_set_null'),
    ]

    operations = [
        migrations.RunPython(fix_linked_asset_content_url, reverse_fix),
    ]
