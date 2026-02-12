import yaml
from typing import Dict, List, Optional
from pathlib import Path
from .models import EntityDefinition, RelationDefinition, EntityMapping, AttributeDefinition

class SemanticService:
    """
    Manages the business ontology and mappings.
    Loads definitions from YAML files.
    """
    
    def __init__(self, config_path: str = "backend/semantic"):
        self.config_path = Path(config_path)
        self.entities: Dict[str, EntityDefinition] = {}
        self.relations: List[RelationDefinition] = []
        self.mappings: Dict[str, EntityMapping] = {}

    def load_definitions(self):
        """
        Load entities, relations, and mappings from YAML files.
        """
        # Ensure directory exists
        if not self.config_path.exists():
            print(f"Warning: Semantic config path {self.config_path} does not exist. Skipping load.")
            return

        # 1. Load Model (Entities & Relations)
        model_file = self.config_path / "model.yaml"
        if model_file.exists():
            with open(model_file, "r") as f:
                data = yaml.safe_load(f) or {}
                
                # Load Entities
                entities_data = data.get("entities", {})
                for name, details in entities_data.items():
                    attrs = [
                        AttributeDefinition(**attr) 
                        for attr in details.get("attributes", [])
                    ]
                    self.entities[name] = EntityDefinition(
                        name=name,
                        label=details.get("label", name),
                        description=details.get("description"),
                        attributes=attrs
                    )
                
                # Load Relations
                relations_data = data.get("relations", [])
                for rel in relations_data:
                    self.relations.append(RelationDefinition(**rel))

        # 2. Load Mappings
        mappings_file = self.config_path / "mappings.yaml"
        if mappings_file.exists():
            with open(mappings_file, "r") as f:
                data = yaml.safe_load(f) or {}
                mappings_data = data.get("mappings", {})
                
                for entity_name, details in mappings_data.items():
                    self.mappings[entity_name] = EntityMapping(
                        entity_name=entity_name,
                        datasource_id=details.get("datasource"),
                        dataset=details.get("dataset"),
                        table=details.get("table"),
                        keys=details.get("keys", []),
                        attributes=details.get("attributes", {})
                    )

    def get_entity(self, name: str) -> Optional[EntityDefinition]:
        return self.entities.get(name)

    def get_mapping(self, entity_name: str) -> Optional[EntityMapping]:
        return self.mappings.get(entity_name)

    def list_entities(self) -> List[EntityDefinition]:
        return list(self.entities.values())