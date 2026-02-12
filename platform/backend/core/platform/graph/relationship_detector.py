from typing import List, Dict, Any, Tuple, Optional
from ..metadata.models import Table, Column
import re

class DetectedRelationship:
    """Represents a detected relationship between two tables."""
    def __init__(
        self,
        from_table_id: str,
        from_column: str,
        to_table_id: str,
        to_column: str,
        confidence: float,
        detection_method: str,
        metadata: Dict[str, Any] = None
    ):
        self.from_table_id = from_table_id
        self.from_column = from_column
        self.to_table_id = to_table_id
        self.to_column = to_column
        self.confidence = confidence
        self.detection_method = detection_method
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_table_id": self.from_table_id,
            "from_column": self.from_column,
            "to_table_id": self.to_table_id,
            "to_column": self.to_column,
            "confidence": self.confidence,
            "detection_method": self.detection_method,
            "metadata": self.metadata
        }


class RelationshipDetector:
    """
    Detects relationships between tables using multiple heuristics:
    1. Naming conventions (e.g., customer_id -> customers.id)
    2. Data type matching
    3. Primary/Foreign key constraints (if available)
    """
    
    def __init__(self):
        # Common ID column patterns
        self.id_patterns = [
            r"^id$",
            r"^(.+)_id$",
            r"^(.+)id$",
            r"^fk_(.+)$",
        ]
        
        # Common primary key patterns
        self.pk_patterns = [
            r"^id$",
            r"^(.+)_id$",
            r"^pk_(.+)$",
        ]
    
    def detect_relationships(
        self,
        tables: List[Table],
        columns_by_table: Dict[str, List[Column]]
    ) -> List[DetectedRelationship]:
        """
        Detect relationships between tables.
        
        Args:
            tables: List of tables to analyze
            columns_by_table: Dictionary mapping table_id to list of columns
            
        Returns:
            List of detected relationships
        """
        relationships = []
        
        # Build lookup structures
        table_by_name = {t.name: t for t in tables}
        
        # For each table, analyze its columns
        for table in tables:
            table_columns = columns_by_table.get(table.id, [])
            
            for column in table_columns:
                # Skip if already marked as foreign key
                if column.is_foreign_key and column.foreign_key_ref:
                    # Add explicit foreign key relationship
                    relationships.append(self._create_fk_relationship(
                        table.id, column, column.foreign_key_ref
                    ))
                    continue
                
                # Try naming convention detection
                detected = self._detect_by_naming_convention(
                    table, column, table_by_name, columns_by_table
                )
                if detected:
                    relationships.extend(detected)
        
        # Remove duplicates and sort by confidence
        relationships = self._deduplicate_relationships(relationships)
        relationships.sort(key=lambda r: r.confidence, reverse=True)
        
        return relationships
    
    def _create_fk_relationship(
        self,
        from_table_id: str,
        from_column: Column,
        fk_ref: str
    ) -> DetectedRelationship:
        """Create relationship from explicit foreign key."""
        # Parse foreign key reference (format: "table_id.column_name")
        parts = fk_ref.split(".")
        to_table_id = ".".join(parts[:-1])
        to_column = parts[-1]
        
        return DetectedRelationship(
            from_table_id=from_table_id,
            from_column=from_column.name,
            to_table_id=to_table_id,
            to_column=to_column,
            confidence=1.0,
            detection_method="explicit_fk",
            metadata={"datatype": from_column.datatype}
        )
    
    def _detect_by_naming_convention(
        self,
        from_table: Table,
        from_column: Column,
        table_by_name: Dict[str, Table],
        columns_by_table: Dict[str, List[Column]]
    ) -> List[DetectedRelationship]:
        """
        Detect relationships using naming conventions.
        
        Examples:
        - customer_id -> customers.id
        - order_id -> orders.id
        - user_id -> users.id
        """
        relationships = []
        column_name = from_column.name.lower()
        
        # Try each pattern
        for pattern in self.id_patterns:
            match = re.match(pattern, column_name)
            if not match:
                continue
            
            # Extract the entity name
            if match.groups():
                entity_name = match.group(1)
            else:
                # Pattern matched but no group (e.g., "id")
                continue
            
            # Try to find matching table
            # Try plural form first (e.g., customer -> customers)
            candidate_tables = [
                entity_name + "s",  # customers
                entity_name,        # customer
                entity_name + "es", # addresses
            ]
            
            for candidate_name in candidate_tables:
                target_table = table_by_name.get(candidate_name)
                if not target_table:
                    continue
                
                # Look for matching primary key column
                target_columns = columns_by_table.get(target_table.id, [])
                
                for target_col in target_columns:
                    # Check if it's a primary key or ID column
                    if target_col.is_primary_key or target_col.name.lower() in ["id", f"{entity_name}_id"]:
                        # Check data type compatibility
                        if self._are_types_compatible(from_column.datatype, target_col.datatype):
                            confidence = self._calculate_confidence(
                                from_column, target_col, entity_name, candidate_name
                            )
                            
                            relationships.append(DetectedRelationship(
                                from_table_id=from_table.id,
                                from_column=from_column.name,
                                to_table_id=target_table.id,
                                to_column=target_col.name,
                                confidence=confidence,
                                detection_method="naming_convention",
                                metadata={
                                    "from_datatype": from_column.datatype,
                                    "to_datatype": target_col.datatype,
                                    "entity_name": entity_name,
                                    "pattern": pattern
                                }
                            ))
        
        return relationships
    
    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two data types are compatible for a relationship."""
        # Normalize types
        t1 = type1.upper()
        t2 = type2.upper()
        
        # Integer types
        int_types = {"INTEGER", "INT64", "BIGINT", "INT", "SMALLINT", "TINYINT"}
        if t1 in int_types and t2 in int_types:
            return True
        
        # String types
        string_types = {"STRING", "VARCHAR", "TEXT", "CHAR", "BPCHAR"}
        if t1 in string_types and t2 in string_types:
            return True
        
        # Exact match
        if t1 == t2:
            return True
        
        return False
    
    def _calculate_confidence(
        self,
        from_column: Column,
        to_column: Column,
        entity_name: str,
        table_name: str
    ) -> float:
        """
        Calculate confidence score for a detected relationship.
        
        Factors:
        - Naming convention match quality
        - Data type match
        - Primary key presence
        """
        confidence = 0.5  # Base confidence for naming match
        
        # Boost if target is primary key
        if to_column.is_primary_key:
            confidence += 0.3
        
        # Boost if exact type match
        if from_column.datatype.upper() == to_column.datatype.upper():
            confidence += 0.1
        
        # Boost if table name is exact plural of entity
        if table_name == entity_name + "s":
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _deduplicate_relationships(
        self,
        relationships: List[DetectedRelationship]
    ) -> List[DetectedRelationship]:
        """Remove duplicate relationships, keeping the highest confidence."""
        seen = {}
        
        for rel in relationships:
            key = (rel.from_table_id, rel.from_column, rel.to_table_id, rel.to_column)
            
            if key not in seen or rel.confidence > seen[key].confidence:
                seen[key] = rel
        
        return list(seen.values())