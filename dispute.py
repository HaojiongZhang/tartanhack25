"""
CourtListener Employment Analysis Library

This library provides tools for analyzing employment-related legal matters
using the CourtListener API. It includes functionality for searching cases,
analyzing patterns, and identifying red flags related to employment practices.

Author: Assistant
Version: 1.0.0
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json
from config import COURT_LISTENER_API_KEY
from llm import summarize_dispute
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CaseType:
    """Data class for defining case types and their priorities"""
    name: str
    priority: int  # 1 (highest) to 3 (lowest)
    nature_of_suit_codes: List[str]
    keywords: List[str]

class CourtListenerConfig:
    """Configuration settings for CourtListener API"""
    BASE_URL = "https://www.courtlistener.com/api/rest/v4"
    
    # Define case types with their nature of suit codes and relevant keywords
    CASE_TYPES = {
        "employment_discrimination": CaseType(
            name="Employment Discrimination",
            priority=1,
            nature_of_suit_codes=["442", "445"],
            keywords=["discrimination", "hostile work environment", "retaliation"]
        ),
        "wage_violations": CaseType(
            name="Wage Violations",
            priority=1,
            nature_of_suit_codes=["710"],
            keywords=["unpaid wages", "overtime", "FLSA"]
        ),
        "workplace_safety": CaseType(
            name="Workplace Safety",
            priority=2,
            nature_of_suit_codes=["790"],
            keywords=["OSHA", "safety violation", "workplace injury"]
        ),
        "bankruptcy": CaseType(
            name="Bankruptcy",
            priority=1,
            nature_of_suit_codes=["422", "423"],
            keywords=["Chapter 11", "bankruptcy", "reorganization"]
        )
    }

class CourtListenerAPI:
    """Main class for interacting with CourtListener API"""
    
    def __init__(self, api_token: str):
        """
        Initialize the API client
        
        Args:
            api_token (str): CourtListener API authentication token
        """
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
    
    def _normalize_company_name(self, company_name: str) -> List[str]:
        """
        Normalize company name and generate variants for searching
        
        Args:
            company_name (str): Original company name
            
        Returns:
            List[str]: List of company name variants to search
        """
        # Common company suffixes
        suffixes = [
            "Inc", "Inc.", "Incorporated",
            "Corp", "Corp.", "Corporation",
            "LLC", "L.L.C.", "Limited Liability Company",
            "Ltd", "Ltd.", "Limited",
            "Co", "Co.", "Company"
        ]
        
        # Basic normalization
        name = company_name.strip()
        base_name = name
        
        # Remove common suffixes to get base name
        for suffix in suffixes:
            if name.endswith(f" {suffix}"):
                base_name = name[:-len(suffix)].strip()
                break
        
        # Generate variants
        variants = [
            name,  # Original name
            base_name,  # Name without suffix
            f'"{name}"',  # Exact match
            f'"{base_name}"'  # Exact match without suffix
        ]
        
        # Add common suffix variants
        for suffix in suffixes:
            variants.append(f"{base_name} {suffix}")
        
        return list(set(variants))  # Remove duplicates

    async def search_cases(
        self,
        company_name: str,
        case_type: CaseType,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Search for cases related to a company and case type
        
        Args:
            company_name (str): Name of the company to search for
            case_type (CaseType): Type of cases to search for
            start_date (str, optional): Start date for search (YYYY-MM-DD)
            end_date (str, optional): End date for search (YYYY-MM-DD)
            
        Returns:
            Dict: Search results from the API
        """
        # Generate company name variants
        name_variants = self._normalize_company_name(company_name)
        
        # Build OR query for name variants
        name_query = " OR ".join(name_variants)
        
        # Build search query
        query = {
            "q": f"({name_query})",
            "type": "r",  # RECAP documents
            "nature_of_suit": case_type.nature_of_suit_codes,
            "order_by": "dateFiled desc",
            "page_size": 500
        }
        
        if start_date:
            query["filed_after"] = start_date
        if end_date:
            query["filed_before"] = end_date
            
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f"{CourtListenerConfig.BASE_URL}/search/",
                params=query
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error searching cases: {response.status}")
                    return {}

class EmploymentAnalyzer:
    """Class for analyzing employment-related legal matters"""
    
    def __init__(self, api_client: CourtListenerAPI):
        """
        Initialize the analyzer
        
        Args:
            api_client (CourtListenerAPI): Initialized API client
        """
        self.api_client = api_client
        
    async def analyze_company(
        self,
        company_name: str,
        lookback_years: int = 3
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a company's employment-related cases
        
        Args:
            company_name (str): Name of the company to analyze
            lookback_years (int): Number of years to look back
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * lookback_years)
        
        results = {
            "company_name": company_name,
            "analysis_date": end_date.isoformat(),
            "lookback_period": f"{lookback_years} years",
            "case_summary": {},
            "red_flags": [],
            "risk_assessment": {
                "overall_risk": "LOW",
                "factors": []
            }
        }
        
        # Analyze each case type
        for case_type in CourtListenerConfig.CASE_TYPES.values():
            cases = await self.api_client.search_cases(
                company_name,
                case_type,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            case_analysis = self._analyze_case_type(cases, case_type)
            results["case_summary"][case_type.name] = case_analysis
            
            # Update red flags and risk assessment
            if case_analysis["total_cases"] > 0:
                self._update_risk_assessment(results, case_analysis, case_type)
        
        return results
    
    def _analyze_case_type(
        self,
        cases: Dict,
        case_type: CaseType
    ) -> Dict[str, Any]:
        """
        Analyze cases of a specific type
        
        Args:
            cases (Dict): Case data from API
            case_type (CaseType): Type of cases being analyzed
            
        Returns:
            Dict[str, Any]: Analysis of cases
        """
        return {
            "total_cases": len(cases.get("results", [])),
            "recent_cases": self._count_recent_cases(cases.get("results", [])),
            "priority_level": case_type.priority,
            "keywords_found": self._analyze_keywords(
                cases.get("results", []),
                case_type.keywords
            )
        }
    
    def _count_recent_cases(self, cases: List[Dict]) -> int:
        """Count cases from the last 12 months"""
        recent_date = datetime.now() - timedelta(days=365)
        count = 0
        for case in cases:
            try:
                date_filed = case.get("dateFiled")
                if date_filed:
                    case_date = datetime.fromisoformat(date_filed)
                    if case_date > recent_date:
                        count += 1
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing date for case: {e}")
        return count
    
    def _analyze_keywords(
        self,
        cases: List[Dict],
        keywords: List[str]
    ) -> Dict[str, int]:
        """Analyze keyword frequency in cases"""
        keyword_counts = {keyword: 0 for keyword in keywords}
        for case in cases:
            text = f"{case.get('case_name', '')} {case.get('description', '')}"
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    keyword_counts[keyword] += 1
        return keyword_counts
    
    def _update_risk_assessment(
        self,
        results: Dict[str, Any],
        case_analysis: Dict[str, Any],
        case_type: CaseType
    ) -> None:
        """Update risk assessment based on case analysis"""
        if case_type.priority == 1 and case_analysis["recent_cases"] > 2:
            results["red_flags"].append(
                f"Multiple recent {case_type.name} cases detected"
            )
            results["risk_assessment"]["overall_risk"] = "HIGH"
            
        if case_analysis["total_cases"] > 5:
            results["risk_assessment"]["factors"].append({
                "factor": f"High volume of {case_type.name} cases",
                "severity": "HIGH"
            })

class EmploymentAnalysisReport:
    """Class for generating reports from analysis results"""
    
    @staticmethod
    def generate_report(analysis_results: Dict[str, Any]) -> str:
        """
        Generate a formatted report from analysis results
        
        Args:
            analysis_results (Dict[str, Any]): Results from EmploymentAnalyzer
            
        Returns:
            str: Formatted report
        """
        report = []
        report.append("Employment Legal Analysis Report")
        report.append("=" * 30)
        report.append(f"\nCompany: {analysis_results['company_name']}")
        report.append(f"Analysis Date: {analysis_results['analysis_date']}")
        report.append(f"Lookback Period: {analysis_results['lookback_period']}")
        
        # Risk Assessment
        report.append("\nRisk Assessment")
        report.append("-" * 15)
        report.append(f"Overall Risk: {analysis_results['risk_assessment']['overall_risk']}")
        
        # Red Flags
        if analysis_results['red_flags']:
            report.append("\nRed Flags")
            report.append("-" * 9)
            for flag in analysis_results['red_flags']:
                report.append(f"- {flag}")
        
        # Case Summary
        report.append("\nCase Summary")
        report.append("-" * 11)
        for case_type, summary in analysis_results['case_summary'].items():
            report.append(f"\n{case_type}:")
            report.append(f"  Total Cases: {summary['total_cases']}")
            report.append(f"  Recent Cases: {summary['recent_cases']}")
            
        return "\n".join(report)

# Example usage
async def get_report(company_name="Microsoft"):
    # Initialize with your API token
    api_client = CourtListenerAPI(COURT_LISTENER_API_KEY)
    analyzer = EmploymentAnalyzer(api_client)
    
    # Analyze a company
    results = await analyzer.analyze_company(company_name, lookback_years=2)
    
    # Generate report
    report = EmploymentAnalysisReport.generate_report(results)
    print(report)
    return report

def get_info(company_name="Microsoft"):
    a = asyncio.run(get_report(company_name))
    
    return summarize_dispute(get_report(a))
    
    
if __name__ == "__main__":
    a = asyncio.run(get_report())
    print(a)
    print("-"*10)
    print(summarize_dispute(a))