from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("eureka", "0030_poiasset_model_transform"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS "eureka_cache_table" (
                    "cache_key" varchar(255) NOT NULL PRIMARY KEY,
                    "value" text NOT NULL,
                    "expires" timestamp with time zone NOT NULL
                );
                CREATE INDEX IF NOT EXISTS "eureka_cache_table_expires" ON "eureka_cache_table" ("expires");
            """,
            reverse_sql='DROP TABLE IF EXISTS "eureka_cache_table";',
        ),
    ]
