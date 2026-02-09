"""
Scoring Engine - Core service for calculating customer health metrics.

This engine implements weighted scoring algorithms for:
- CNS (Client Net Score): Overall customer satisfaction/health
- Churn Probability: Risk of customer leaving
- Health Score: Combined metric for quick assessment

All scores range from 0.0 (worst) to 1.0 (best), except churn which is
0.0 (no risk) to 1.0 (high risk).
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta


class ScoringEngine:
    """
    Core scoring engine for calculating customer health metrics.

    Scoring Methodology:

    CNS (Client Net Score) - Weighted factors:
      - Payment Health (40%): Invoice payment behavior
      - Engagement Level (30%): Interaction frequency and sentiment
      - Financial Health (20%): MRR stability
      - Account Maturity (10%): Customer tenure

    Churn Probability - Risk indicators:
      - Payment Issues (35%): Overdue/unpaid invoices
      - Engagement Drop (30%): Declining interactions, negative sentiment
      - Financial Decline (25%): Decreasing MRR
      - Support Issues (10%): High volume of negative interactions
    """

    # Configurable weights for CNS calculation
    CNS_WEIGHTS = {
        'payment_health': 0.40,
        'engagement': 0.30,
        'financial_health': 0.20,
        'account_maturity': 0.10
    }

    # Configurable weights for Churn calculation
    CHURN_WEIGHTS = {
        'payment_issues': 0.35,
        'engagement_drop': 0.30,
        'financial_decline': 0.25,
        'support_issues': 0.10
    }

    @staticmethod
    def _calculate_payment_health(invoices: List[Dict[str, Any]]) -> float:
        """
        Calculate payment health score based on invoice payment behavior.

        Factors:
        - Percentage of paid invoices
        - On-time payment rate
        - No overdue invoices

        Returns:
            Score from 0.0 to 1.0
        """
        if not invoices:
            return 0.5  # Neutral score if no invoice data

        total_invoices = len(invoices)
        paid_invoices = sum(1 for inv in invoices if inv.get('status') == 'paid')
        overdue_invoices = sum(1 for inv in invoices if inv.get('status') in ['overdue', 'pending'])

        # Payment rate (0.0 to 1.0)
        payment_rate = paid_invoices / total_invoices if total_invoices > 0 else 0.5

        # Penalty for overdue invoices
        overdue_penalty = min(overdue_invoices * 0.15, 0.5)

        score = max(0.0, min(1.0, payment_rate - overdue_penalty))
        return score

    @staticmethod
    def _calculate_engagement_score(interactions: List[Dict[str, Any]]) -> float:
        """
        Calculate engagement score based on interaction frequency and sentiment.

        Factors:
        - Recent interaction frequency (last 90 days)
        - Positive sentiment ratio
        - Interaction variety

        Returns:
            Score from 0.0 to 1.0
        """
        if not interactions:
            return 0.3  # Low score if no interaction data

        now = datetime.now()
        recent_cutoff = now - timedelta(days=90)

        # Count recent interactions
        recent_interactions = []
        for interaction in interactions:
            created_at = interaction.get('created_at')
            if created_at:
                # Handle both string and datetime objects
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        continue
                if created_at >= recent_cutoff:
                    recent_interactions.append(interaction)

        # Frequency score (normalized to 0-1, assuming 10+ interactions is excellent)
        frequency_score = min(len(recent_interactions) / 10, 1.0)

        # Sentiment score
        if recent_interactions:
            positive_count = sum(1 for i in recent_interactions if i.get('sentiment') == 'positive')
            neutral_count = sum(1 for i in recent_interactions if i.get('sentiment') == 'neutral')
            negative_count = sum(1 for i in recent_interactions if i.get('sentiment') == 'negative')

            total_with_sentiment = positive_count + neutral_count + negative_count
            if total_with_sentiment > 0:
                # Positive = 1.0, Neutral = 0.5, Negative = 0.0
                sentiment_score = (positive_count + neutral_count * 0.5) / total_with_sentiment
            else:
                sentiment_score = 0.5
        else:
            sentiment_score = 0.5

        # Combined engagement score (70% frequency, 30% sentiment)
        score = (frequency_score * 0.7) + (sentiment_score * 0.3)
        return max(0.0, min(1.0, score))

    @staticmethod
    def _calculate_financial_health(mrr: float) -> float:
        """
        Calculate financial health score based on MRR.

        For now, this is a simple normalization. In future iterations,
        this could track MRR trends over time.

        Args:
            mrr: Monthly Recurring Revenue

        Returns:
            Score from 0.0 to 1.0
        """
        if mrr is None or mrr <= 0:
            return 0.2

        # Normalize MRR to 0-1 scale
        # Assuming MRR ranges: <$1k = low, $5k = medium, $10k+ = high
        if mrr < 1000:
            score = 0.3 + (mrr / 1000) * 0.2  # 0.3 to 0.5
        elif mrr < 5000:
            score = 0.5 + ((mrr - 1000) / 4000) * 0.3  # 0.5 to 0.8
        else:
            score = 0.8 + min((mrr - 5000) / 10000, 0.2)  # 0.8 to 1.0

        return max(0.0, min(1.0, score))

    @staticmethod
    def _calculate_account_maturity(created_at: Any) -> float:
        """
        Calculate account maturity score based on customer tenure.

        Longer tenured customers are typically more stable.

        Returns:
            Score from 0.0 to 1.0
        """
        if not created_at:
            return 0.5

        try:
            # Handle both string and datetime objects
            if isinstance(created_at, str):
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_dt = created_at

            tenure_days = (datetime.now() - created_dt).days

            # Normalize tenure (0-365 days = 0.5-1.0)
            if tenure_days < 30:
                score = 0.3  # Very new customer
            elif tenure_days < 90:
                score = 0.5  # New customer
            elif tenure_days < 365:
                score = 0.5 + (tenure_days - 90) / (365 - 90) * 0.3  # 0.5 to 0.8
            else:
                score = 0.8 + min((tenure_days - 365) / 730, 0.2)  # 0.8 to 1.0

            return max(0.0, min(1.0, score))
        except:
            return 0.5

    @staticmethod
    def calculate_cns(customer_data: Dict[str, Any]) -> float:
        """
        Calculate Client Net Score (CNS).

        This is a weighted score combining multiple health factors:
        - Payment health (40%)
        - Engagement level (30%)
        - Financial health (20%)
        - Account maturity (10%)

        Args:
            customer_data: Dictionary containing:
                - invoices: List of invoice dicts
                - interactions: List of interaction dicts
                - mrr: Monthly recurring revenue
                - created_at: Account creation date

        Returns:
            CNS score between 0.0 and 1.0
        """
        invoices = customer_data.get('invoices', [])
        interactions = customer_data.get('interactions', [])
        mrr = customer_data.get('mrr', 0)
        created_at = customer_data.get('created_at')

        # Calculate individual components
        payment_health = ScoringEngine._calculate_payment_health(invoices)
        engagement = ScoringEngine._calculate_engagement_score(interactions)
        financial_health = ScoringEngine._calculate_financial_health(mrr)
        account_maturity = ScoringEngine._calculate_account_maturity(created_at)

        # Apply weights
        cns = (
            payment_health * ScoringEngine.CNS_WEIGHTS['payment_health'] +
            engagement * ScoringEngine.CNS_WEIGHTS['engagement'] +
            financial_health * ScoringEngine.CNS_WEIGHTS['financial_health'] +
            account_maturity * ScoringEngine.CNS_WEIGHTS['account_maturity']
        )

        return round(cns, 3)

    @staticmethod
    def _calculate_payment_risk(invoices: List[Dict[str, Any]]) -> float:
        """
        Calculate payment risk (inverse of payment health).

        Returns:
            Risk score from 0.0 (no risk) to 1.0 (high risk)
        """
        if not invoices:
            return 0.3  # Moderate risk if no invoice data

        total_invoices = len(invoices)
        unpaid_invoices = sum(1 for inv in invoices if inv.get('status') in ['pending', 'overdue'])
        overdue_invoices = sum(1 for inv in invoices if inv.get('status') == 'overdue')

        # Calculate unpaid rate
        unpaid_rate = unpaid_invoices / total_invoices if total_invoices > 0 else 0.3

        # Extra penalty for overdue
        overdue_penalty = min(overdue_invoices * 0.2, 0.5)

        risk = min(1.0, unpaid_rate + overdue_penalty)
        return risk

    @staticmethod
    def _calculate_engagement_risk(interactions: List[Dict[str, Any]]) -> float:
        """
        Calculate engagement risk based on declining interactions and sentiment.

        Returns:
            Risk score from 0.0 (no risk) to 1.0 (high risk)
        """
        if not interactions:
            return 0.6  # High risk if no interactions

        now = datetime.now()
        recent_cutoff = now - timedelta(days=30)
        older_cutoff = now - timedelta(days=90)

        # Count interactions in different time windows
        recent_count = 0
        older_count = 0
        negative_count = 0

        for interaction in interactions:
            created_at = interaction.get('created_at')
            sentiment = interaction.get('sentiment')

            if created_at:
                try:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

                    if created_at >= recent_cutoff:
                        recent_count += 1
                    elif created_at >= older_cutoff:
                        older_count += 1

                    if sentiment == 'negative':
                        negative_count += 1
                except:
                    pass

        # Declining interaction risk (comparing recent vs older periods)
        if older_count > 0:
            decline_ratio = 1.0 - (recent_count / older_count)
            decline_risk = max(0.0, decline_ratio * 0.6)  # Max 0.6 contribution
        else:
            decline_risk = 0.4 if recent_count == 0 else 0.2

        # Negative sentiment risk
        total_interactions = len(interactions)
        sentiment_risk = min((negative_count / total_interactions) * 0.8, 0.4) if total_interactions > 0 else 0.2

        risk = min(1.0, decline_risk + sentiment_risk)
        return risk

    @staticmethod
    def _calculate_financial_risk(mrr: float) -> float:
        """
        Calculate financial risk based on MRR level.

        Low MRR = higher risk. In future, this could track MRR trends.

        Returns:
            Risk score from 0.0 (no risk) to 1.0 (high risk)
        """
        if mrr is None or mrr <= 0:
            return 0.8  # High risk if no MRR

        # Inverse of financial health
        if mrr < 1000:
            risk = 0.7 - (mrr / 1000) * 0.4  # 0.7 to 0.3
        elif mrr < 5000:
            risk = 0.3 - ((mrr - 1000) / 4000) * 0.2  # 0.3 to 0.1
        else:
            risk = max(0.05, 0.1 - (mrr - 5000) / 50000)  # 0.1 to 0.05

        return max(0.0, min(1.0, risk))

    @staticmethod
    def _calculate_support_risk(interactions: List[Dict[str, Any]]) -> float:
        """
        Calculate support risk based on support ticket volume and sentiment.

        Returns:
            Risk score from 0.0 (no risk) to 1.0 (high risk)
        """
        if not interactions:
            return 0.2

        support_tickets = [i for i in interactions if i.get('type') == 'support_ticket']

        if not support_tickets:
            return 0.1  # Low risk if no support tickets

        # High volume of support tickets
        volume_risk = min(len(support_tickets) / 20, 0.5)  # Max 0.5

        # Negative sentiment in tickets
        negative_tickets = sum(1 for t in support_tickets if t.get('sentiment') == 'negative')
        sentiment_risk = (negative_tickets / len(support_tickets)) * 0.5 if len(support_tickets) > 0 else 0

        risk = min(1.0, volume_risk + sentiment_risk)
        return risk

    @staticmethod
    def calculate_churn_probability(customer_data: Dict[str, Any]) -> float:
        """
        Calculate churn probability.

        This is a weighted risk score combining multiple risk factors:
        - Payment issues (35%)
        - Engagement drop (30%)
        - Financial decline (25%)
        - Support issues (10%)

        Args:
            customer_data: Dictionary containing customer information

        Returns:
            Churn probability between 0.0 (no risk) and 1.0 (high risk)
        """
        invoices = customer_data.get('invoices', [])
        interactions = customer_data.get('interactions', [])
        mrr = customer_data.get('mrr', 0)

        # Calculate individual risk components
        payment_risk = ScoringEngine._calculate_payment_risk(invoices)
        engagement_risk = ScoringEngine._calculate_engagement_risk(interactions)
        financial_risk = ScoringEngine._calculate_financial_risk(mrr)
        support_risk = ScoringEngine._calculate_support_risk(interactions)

        # Apply weights
        churn_prob = (
            payment_risk * ScoringEngine.CHURN_WEIGHTS['payment_issues'] +
            engagement_risk * ScoringEngine.CHURN_WEIGHTS['engagement_drop'] +
            financial_risk * ScoringEngine.CHURN_WEIGHTS['financial_decline'] +
            support_risk * ScoringEngine.CHURN_WEIGHTS['support_issues']
        )

        return round(churn_prob, 3)

    @staticmethod
    def calculate_health_score(customer_data: Dict[str, Any]) -> float:
        """
        Calculate overall customer health score.

        This combines CNS and churn probability into a single metric.
        Formula: health = CNS * (1 - churn_probability)

        Args:
            customer_data: Dictionary containing customer information

        Returns:
            Health score between 0.0 and 1.0
        """
        cns = ScoringEngine.calculate_cns(customer_data)
        churn = ScoringEngine.calculate_churn_probability(customer_data)

        # Combined formula: high CNS and low churn = high health
        health = cns * (1 - churn)

        return round(health, 3)


# Global instance
_scoring_engine_instance: ScoringEngine = None


def get_scoring_engine() -> ScoringEngine:
    """
    Get the global ScoringEngine instance.

    Returns:
        ScoringEngine instance
    """
    global _scoring_engine_instance
    if _scoring_engine_instance is None:
        _scoring_engine_instance = ScoringEngine()
    return _scoring_engine_instance
