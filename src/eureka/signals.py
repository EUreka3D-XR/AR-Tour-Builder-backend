from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models.poi import POI

@receiver([post_save, post_delete], sender=POI)
def update_tour_bounding_box(sender, instance, **kwargs):
    """
    Update the tour's bounding box and center whenever a POI is created, updated, or deleted.
    """
    # Get the tour associated with this POI
    tour = instance.tour

    # Update the tour's bounding box and center
    tour.update_bounding_box() 