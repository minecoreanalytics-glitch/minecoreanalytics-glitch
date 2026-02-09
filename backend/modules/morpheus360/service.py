import json
import os
from typing import List, Optional, Dict
from datetime import datetime
import uuid
from .models import Portfolio

class PortfolioService:
    def __init__(self, storage_path: str = "data/portfolios.json"):
        self.storage_path = storage_path
        self._ensure_storage()
        self.portfolios: Dict[str, Portfolio] = self._load()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)

    def _load(self) -> Dict[str, Portfolio]:
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return {k: Portfolio(**v) for k, v in data.items()}
        except Exception as e:
            print(f"Error loading portfolios: {e}")
            return {}

    def _save(self):
        try:
            with open(self.storage_path, 'w') as f:
                data = {k: v.model_dump(mode='json') for k, v in self.portfolios.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving portfolios: {e}")

    def create_portfolio(self, name: str, description: Optional[str] = None, account_ids: List[str] = []) -> Portfolio:
        portfolio_id = str(uuid.uuid4())
        now = datetime.now()
        portfolio = Portfolio(
            id=portfolio_id,
            name=name,
            description=description,
            account_ids=account_ids,
            created_at=now,
            updated_at=now
        )
        self.portfolios[portfolio_id] = portfolio
        self._save()
        return portfolio

    def list_portfolios(self) -> List[Portfolio]:
        return list(self.portfolios.values())

    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        return self.portfolios.get(portfolio_id)

    def update_portfolio(self, portfolio_id: str, name: Optional[str] = None, description: Optional[str] = None, account_ids: Optional[List[str]] = None) -> Optional[Portfolio]:
        if portfolio_id not in self.portfolios:
            return None
        
        portfolio = self.portfolios[portfolio_id]
        if name is not None:
            portfolio.name = name
        if description is not None:
            portfolio.description = description
        if account_ids is not None:
            portfolio.account_ids = account_ids
        
        portfolio.updated_at = datetime.now()
        self._save()
        return portfolio

    def delete_portfolio(self, portfolio_id: str) -> bool:
        if portfolio_id in self.portfolios:
            del self.portfolios[portfolio_id]
            self._save()
            return True
        return False

# Global instance
portfolio_service = PortfolioService()
