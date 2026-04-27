from typing import Type, List, Dict
from django.db import models

def create_bulk_items(
    main_model: Type[models.Model],
    child_model: Type[models.Model],
    main_data: Dict,
    children_data: List[Dict],
    foreign_key_name=None
):
   
    """
    Creates a main_model instance and bulk creates related child_model instances.

    Args:
        main_model (Model): The Django model class for the main object.
        child_model (Model): The Django model class for the child objects.
        main_data (dict): Data for creating the main object.
        children_data (list of dict): List of data dicts for the child objects.
        foreign_key_name (str): The name of the foreign key field in the child model that links to the main model.

    Returns:
        The created main_model instance.
    """
   
    main_instance = main_model.objects.create(**main_data)

    items = [
        child_model(**{foreign_key_name: main_instance, **item})
        for item in children_data
    ]

    child_model.objects.bulk_create(items)
    return main_instance