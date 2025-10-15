from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models.poi import POI

@receiver([post_save, post_delete], sender=POI)
def update_tour_bounding_box(sender, instance, **kwargs):
    """
    Update the tour's bounding box whenever a POI is created, updated, or deleted.
    """
    # Get the tour associated with this POI
    tour = instance.tour
    
    # Update the tour's bounding box
    tour.update_bounding_box() 