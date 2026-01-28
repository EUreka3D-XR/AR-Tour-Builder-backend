from django.db import migrations


def fix_linked_asset_structure(apps, schema_editor):
    """
    Fix linked_asset data:
    1. Convert old structure (locales first) to new structure (fields first)
    2. Rename 'content_url' to 'url' if present

    Old structure:
    {
        "locales": {
            "en": {"title": "...", "url": "..."},
            "fr": {"title": "...", "url": "..."}
        }
    }

    New structure:
    {
        "title": {"locales": {"en": "...", "fr": "..."}},
        "url": {"locales": {"en": "...", "fr": "..."}}
    }
    """
    POIAsset = apps.get_model('eureka', 'POIAsset')

    for poi_asset in POIAsset.objects.exclude(linked_asset__isnull=True):
        if not poi_asset.linked_asset:
            continue

        linked_asset = poi_asset.linked_asset
        updated = False

        # Check if it's the old structure (has 'locales' at root with nested title/url)
        if 'locales' in linked_asset and isinstance(linked_asset.get('locales'), dict):
            # Old structure detected - convert to new structure
            old_locales = linked_asset['locales']
            new_structure = {
                'title': {'locales': {}},
                'url': {'locales': {}}
            }

            for locale_code, data in old_locales.items():
                if isinstance(data, dict):
                    if 'title' in data:
                        new_structure['title']['locales'][locale_code] = data['title']
                    # Handle both 'url' and 'content_url'
                    if 'url' in data:
                        new_structure['url']['locales'][locale_code] = data['url']
                    elif 'content_url' in data:
                        new_structure['url']['locales'][locale_code] = data['content_url']

            poi_asset.linked_asset = new_structure
            updated = True

        # Check if it's the new structure but with 'content_url' instead of 'url'
        elif 'content_url' in linked_asset and 'url' not in linked_asset:
            linked_asset['url'] = linked_asset.pop('content_url')
            updated = True

        if updated:
            poi_asset.save(update_fields=['linked_asset'])


def reverse_fix(apps, schema_editor):
    """
    Reverse: convert new structure back to old structure.
    Note: This loses the content_url -> url rename information.
    """
    POIAsset = apps.get_model('eureka', 'POIAsset')

    for poi_asset in POIAsset.objects.exclude(linked_asset__isnull=True):
        if not poi_asset.linked_asset:
            continue

        linked_asset = poi_asset.linked_asset

        # Check if it's the new structure (has 'title' and 'url' at root)
        if 'title' in linked_asset and 'url' in linked_asset:
            title_locales = linked_asset.get('title', {}).get('locales', {})
            url_locales = linked_asset.get('url', {}).get('locales', {})

            # Get all locale codes
            all_locales = set(title_locales.keys()) | set(url_locales.keys())

            old_structure = {'locales': {}}
            for locale_code in all_locales:
                old_structure['locales'][locale_code] = {
                    'title': title_locales.get(locale_code, ''),
                    'url': url_locales.get(locale_code, '')
                }

            poi_asset.linked_asset = old_structure
            poi_asset.save(update_fields=['linked_asset'])


class Migration(migrations.Migration):
    dependencies = [
        ('eureka', '0027_fix_linked_asset_url_key'),
    ]

    operations = [
        migrations.RunPython(fix_linked_asset_structure, reverse_fix),
    ]
