from django.db import migrations
import eureka.models.fields


def migrate_coordinates_to_georeference(apps, schema_editor):
    """
    Transform coordinates data from old structure to new georeference structure.

    Old structure:
    {
        "lat": 37.9838,
        "long": 23.7275
    }

    New structure:
    {
        "coordinates": {
            "lat": 37.9838,
            "long": 23.7275
        }
    }
    """
    Asset = apps.get_model('eureka', 'Asset')
    POIAsset = apps.get_model('eureka', 'POIAsset')

    # Migrate Asset coordinates
    for asset in Asset.objects.exclude(coordinates__isnull=True):
        if asset.coordinates and isinstance(asset.coordinates, dict):
            # Check if it's the old format (has lat/long at root level)
            if 'lat' in asset.coordinates and 'long' in asset.coordinates and 'coordinates' not in asset.coordinates:
                asset.coordinates = {'coordinates': asset.coordinates}
                asset.save(update_fields=['coordinates'])

    # Migrate POIAsset coordinates
    for poi_asset in POIAsset.objects.exclude(coordinates__isnull=True):
        if poi_asset.coordinates and isinstance(poi_asset.coordinates, dict):
            # Check if it's the old format (has lat/long at root level)
            if 'lat' in poi_asset.coordinates and 'long' in poi_asset.coordinates and 'coordinates' not in poi_asset.coordinates:
                poi_asset.coordinates = {'coordinates': poi_asset.coordinates}
                poi_asset.save(update_fields=['coordinates'])


def reverse_migrate_georeference_to_coordinates(apps, schema_editor):
    """
    Reverse: transform georeference data back to old coordinates structure.
    """
    Asset = apps.get_model('eureka', 'Asset')
    POIAsset = apps.get_model('eureka', 'POIAsset')

    # Reverse Asset georeference
    for asset in Asset.objects.exclude(georeference__isnull=True):
        if asset.georeference and isinstance(asset.georeference, dict):
            if 'coordinates' in asset.georeference:
                asset.georeference = asset.georeference['coordinates']
                asset.save(update_fields=['georeference'])

    # Reverse POIAsset georeference
    for poi_asset in POIAsset.objects.exclude(georeference__isnull=True):
        if poi_asset.georeference and isinstance(poi_asset.georeference, dict):
            if 'coordinates' in poi_asset.georeference:
                poi_asset.georeference = poi_asset.georeference['coordinates']
                poi_asset.save(update_fields=['georeference'])


class Migration(migrations.Migration):
    dependencies = [
        ('eureka', '0028_fix_linked_asset_structure'),
    ]

    operations = [
        # First, run the data migration to transform existing coordinates to new structure
        migrations.RunPython(migrate_coordinates_to_georeference, reverse_migrate_georeference_to_coordinates),

        # Then rename the field on Asset model
        migrations.RenameField(
            model_name='asset',
            old_name='coordinates',
            new_name='georeference',
        ),

        # Rename the field on POIAsset model
        migrations.RenameField(
            model_name='poiasset',
            old_name='coordinates',
            new_name='georeference',
        ),

        # Alter the field type to use the new Georeference field on Asset
        migrations.AlterField(
            model_name='asset',
            name='georeference',
            field=eureka.models.fields.Georeference(blank=True, help_text='Georeference with coordinates (optional)', null=True),
        ),

        # Alter the field type to use the new Georeference field on POIAsset
        migrations.AlterField(
            model_name='poiasset',
            name='georeference',
            field=eureka.models.fields.Georeference(blank=True, help_text='Georeference with coordinates (optional)', null=True),
        ),
    ]
