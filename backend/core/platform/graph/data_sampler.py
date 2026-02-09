from typing import List, Dict, Any, Optional, Set
from ..connectors.base import BaseConnector
from ..metadata.models import Table, Column

class DataSampleResult:
    """Results from sampling a table's data."""
    def __init__(
        self,
        table_id: str,
        column_name: str,
        sample_values: List[Any],
        distinct_count: int,
        null_count: int,
        total_count: int,
        cardinality_ratio: float
    ):
        self.table_id = table_id
        self.column_name = column_name
        self.sample_values = sample_values
        self.distinct_count = distinct_count
        self.null_count = null_count
        self.total_count = total_count
        self.cardinality_ratio = cardinality_ratio
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_id": self.table_id,
            "column_name": self.column_name,
            "sample_values": self.sample_values,
            "distinct_count": self.distinct_count,
            "null_count": self.null_count,
            "total_count": self.total_count,
            "cardinality_ratio": self.cardinality_ratio
        }


class DataSampler:
    """
    Samples data from tables to detect relationships through data analysis.
    
    Techniques:
    1. Cardinality analysis (1:1, 1:N, N:M)
    2. Value overlap detection
    3. Distribution analysis
    """
    
    def __init__(self, connector: BaseConnector, sample_size: int = 1000):
        self.connector = connector
        self.sample_size = sample_size
    
    def sample_column(
        self,
        dataset_id: str,
        table_name: str,
        column_name: str
    ) -> Optional[DataSampleResult]:
        """
        Sample data from a specific column.
        
        Args:
            dataset_id: Dataset identifier
            table_name: Table name
            column_name: Column name
            
        Returns:
            DataSampleResult with statistics and sample values
        """
        try:
            # Build the full table reference
            table_id = f"{dataset_id}.{table_name}"
            
            # Query for statistics and sample
            query = f"""
            WITH stats AS (
                SELECT
                    COUNT(*) as total_count,
                    COUNT(DISTINCT `{column_name}`) as distinct_count,
                    COUNTIF(`{column_name}` IS NULL) as null_count
                FROM `{dataset_id}.{table_name}`
            ),
            samples AS (
                SELECT DISTINCT `{column_name}` as value
                FROM `{dataset_id}.{table_name}`
                WHERE `{column_name}` IS NOT NULL
                LIMIT {self.sample_size}
            )
            SELECT
                stats.total_count,
                stats.distinct_count,
                stats.null_count,
                ARRAY_AGG(samples.value LIMIT {min(100, self.sample_size)}) as sample_values
            FROM stats
            CROSS JOIN samples
            GROUP BY stats.total_count, stats.distinct_count, stats.null_count
            """
            
            results = self.connector.execute_query(query)
            
            if not results:
                return None
            
            row = results[0]
            total_count = row.get("total_count", 0)
            distinct_count = row.get("distinct_count", 0)
            null_count = row.get("null_count", 0)
            sample_values = row.get("sample_values", [])
            
            # Calculate cardinality ratio
            cardinality_ratio = distinct_count / total_count if total_count > 0 else 0
            
            return DataSampleResult(
                table_id=table_id,
                column_name=column_name,
                sample_values=sample_values,
                distinct_count=distinct_count,
                null_count=null_count,
                total_count=total_count,
                cardinality_ratio=cardinality_ratio
            )
            
        except Exception as e:
            print(f"Error sampling column {dataset_id}.{table_name}.{column_name}: {e}")
            return None
    
    def detect_value_overlap(
        self,
        sample1: DataSampleResult,
        sample2: DataSampleResult
    ) -> float:
        """
        Calculate the overlap between two column samples.
        
        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        if not sample1.sample_values or not sample2.sample_values:
            return 0.0
        
        set1 = set(sample1.sample_values)
        set2 = set(sample2.sample_values)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def analyze_cardinality(
        self,
        from_sample: DataSampleResult,
        to_sample: DataSampleResult
    ) -> str:
        """
        Determine the cardinality of a relationship.
        
        Returns:
            "1:1", "1:N", "N:1", or "N:M"
        """
        # High cardinality ratio (close to 1.0) suggests unique values
        from_is_unique = from_sample.cardinality_ratio > 0.95
        to_is_unique = to_sample.cardinality_ratio > 0.95
        
        if from_is_unique and to_is_unique:
            return "1:1"
        elif from_is_unique and not to_is_unique:
            return "N:1"
        elif not from_is_unique and to_is_unique:
            return "1:N"
        else:
            return "N:M"
    
    def validate_relationship(
        self,
        dataset_id: str,
        from_table: str,
        from_column: str,
        to_table: str,
        to_column: str
    ) -> Dict[str, Any]:
        """
        Validate a potential relationship by checking data overlap.
        
        Returns:
            Dictionary with validation results including overlap percentage
        """
        try:
            # Sample both columns
            from_sample = self.sample_column(dataset_id, from_table, from_column)
            to_sample = self.sample_column(dataset_id, to_table, to_column)
            
            if not from_sample or not to_sample:
                return {
                    "valid": False,
                    "error": "Could not sample columns"
                }
            
            # Calculate overlap
            overlap = self.detect_value_overlap(from_sample, to_sample)
            
            # Determine cardinality
            cardinality = self.analyze_cardinality(from_sample, to_sample)
            
            # A relationship is likely valid if there's significant overlap
            is_valid = overlap > 0.1  # At least 10% overlap
            
            return {
                "valid": is_valid,
                "overlap_ratio": overlap,
                "cardinality": cardinality,
                "from_stats": {
                    "distinct_count": from_sample.distinct_count,
                    "total_count": from_sample.total_count,
                    "cardinality_ratio": from_sample.cardinality_ratio
                },
                "to_stats": {
                    "distinct_count": to_sample.distinct_count,
                    "total_count": to_sample.total_count,
                    "cardinality_ratio": to_sample.cardinality_ratio
                }
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def get_column_profile(
        self,
        dataset_id: str,
        table_name: str,
        column_name: str
    ) -> Dict[str, Any]:
        """
        Get a comprehensive profile of a column.
        
        Returns:
            Dictionary with column statistics and characteristics
        """
        sample = self.sample_column(dataset_id, table_name, column_name)
        
        if not sample:
            return {"error": "Could not sample column"}
        
        # Determine if column looks like a key
        is_likely_key = sample.cardinality_ratio > 0.95 and sample.null_count == 0
        
        # Determine if column looks like a foreign key
        is_likely_fk = (
            0.3 < sample.cardinality_ratio < 0.95 and
            sample.null_count < sample.total_count * 0.1  # Less than 10% nulls
        )
        
        return {
            "table_id": sample.table_id,
            "column_name": sample.column_name,
            "total_count": sample.total_count,
            "distinct_count": sample.distinct_count,
            "null_count": sample.null_count,
            "cardinality_ratio": sample.cardinality_ratio,
            "is_likely_key": is_likely_key,
            "is_likely_fk": is_likely_fk,
            "sample_values": sample.sample_values[:10]  # First 10 samples
        }