"""
DynamoDB access layer with Boto3 client and CRUD operations.
"""

import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from app.core.config import Config
from app.models.database import ScanModel, FindingModel, RepairModel, VerificationResultModel


logger = logging.getLogger("accesslens.db")


class DynamoDBError(Exception):
    """Custom exception for DynamoDB errors."""
    pass


class DynamoDBClient:
    """DynamoDB client wrapper with connection pooling."""
    
    def __init__(self, config: Config):
        self.config = config
        self._client = None
        self._resource = None
    
    @property
    def client(self):
        """Get or create Boto3 DynamoDB client."""
        if self._client is None:
            kwargs = {"region_name": self.config.AWS_REGION}
            if self.config.USE_LOCAL_DYNAMODB:
                kwargs["endpoint_url"] = self.config.LOCAL_DYNAMODB_ENDPOINT
            self._client = boto3.client("dynamodb", **kwargs)
            logger.info("DynamoDB client initialized")
        return self._client
    
    @property
    def resource(self):
        """Get or create Boto3 DynamoDB resource."""
        if self._resource is None:
            kwargs = {"region_name": self.config.AWS_REGION}
            if self.config.USE_LOCAL_DYNAMODB:
                kwargs["endpoint_url"] = self.config.LOCAL_DYNAMODB_ENDPOINT
            self._resource = boto3.resource("dynamodb", **kwargs)
        return self._resource


class ScansRepository:
    """CRUD for Scans table."""
    
    def __init__(self, db: DynamoDBClient, config: Config):
        self.db = db
        self.table_name = config.DYNAMODB_TABLE_SCANS
        self.table = db.resource.Table(self.table_name)
    
    def create(self, scan: ScanModel) -> ScanModel:
        """Create a new scan."""
        try:
            self.table.put_item(Item=scan.to_dynamodb_item())
            logger.info(f"Scan created: {scan.scan_id}")
            return scan
        except ClientError as e:
            logger.error(f"Create scan failed: {e}")
            raise DynamoDBError("Create scan failed")
    
    def get(self, scan_id: str) -> Optional[ScanModel]:
        """Get scan by ID."""
        try:
            response = self.table.get_item(Key={"scan_id": scan_id})
            if "Item" not in response:
                return None
            return ScanModel(**response["Item"])
        except ClientError as e:
            logger.error(f"Get scan failed: {e}")
            raise DynamoDBError("Get scan failed")


class FindingsRepository:
    """CRUD for Findings table."""
    
    def __init__(self, db: DynamoDBClient, config: Config):
        self.db = db
        self.table_name = config.DYNAMODB_TABLE_FINDINGS
        self.table = db.resource.Table(self.table_name)
    
    def create(self, finding: FindingModel) -> FindingModel:
        """Create a finding."""
        try:
            self.table.put_item(Item=finding.to_dynamodb_item())
            logger.info(f"Finding created: {finding.finding_id}")
            return finding
        except ClientError as e:
            logger.error(f"Create finding failed: {e}")
            raise DynamoDBError("Create finding failed")
    
    def query_by_scan(self, scan_id: str) -> list:
        """Get all findings for a scan."""
        try:
            response = self.table.query(
                KeyConditionExpression="scan_id = :scan_id",
                ExpressionAttributeValues={":scan_id": scan_id}
            )
            return [FindingModel(**item) for item in response.get("Items", [])]
        except ClientError as e:
            logger.error(f"Query findings failed: {e}")
            raise DynamoDBError("Query findings failed")


class RepairsRepository:
    """CRUD for Repairs table."""
    
    def __init__(self, db: DynamoDBClient, config: Config):
        self.db = db
        self.table_name = config.DYNAMODB_TABLE_REPAIRS
        self.table = db.resource.Table(self.table_name)
    
    def create(self, repair: RepairModel) -> RepairModel:
        """Create a repair."""
        try:
            self.table.put_item(Item=repair.to_dynamodb_item())
            logger.info(f"Repair created: {repair.repair_id}")
            return repair
        except ClientError as e:
            logger.error(f"Create repair failed: {e}")
            raise DynamoDBError("Create repair failed")


class VerificationRepository:
    """CRUD for VerificationResults table."""
    
    def __init__(self, db: DynamoDBClient, config: Config):
        self.db = db
        self.table_name = config.DYNAMODB_TABLE_VERIFICATION
        self.table = db.resource.Table(self.table_name)
    
    def create(self, result: VerificationResultModel) -> VerificationResultModel:
        """Create verification result."""
        try:
            self.table.put_item(Item=result.to_dynamodb_item())
            logger.info(f"Verification created: {result.verification_id}")
            return result
        except ClientError as e:
            logger.error(f"Create verification failed: {e}")
            raise DynamoDBError("Create verification failed")