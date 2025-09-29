"""
Enhanced Llama4 Service for local AI processing
Integrates with existing architecture and provides text parsing for spending entries
Cost-free alternative to OpenAI with full local processing
"""

import logging
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from models.spending_models import (
    NLPResult, OCRResult, SpendingEntry, AIAnalysis, 
    AIInsight, AIRecommendation, AIAnomaly,
    SpendingCategory, PaymentMethod
)

logger = logging.getLogger(__name__)

class EnhancedLlamaService:
    """Enhanced Llama service with proper integration"""
    
    def __init__(self, settings):
        self.settings = settings
        self.ollama_url = getattr(settings, 'ollama_url', 'http://localhost:11434')
        self.model = getattr(settings, 'llama_model', 'llama3.2:3b')  # Use Llama 3.2 3B
        self.max_retries = 3
        self.request_timeout = 60
        self.initialized = False
        self._initialize()
    
    def _initialize(self):
        """Initialize the service"""
        try:
            logger.info("🦙 Initializing Enhanced Llama Service...")
            self.system_prompts = self._create_system_prompts()
            self.initialized = True
            logger.info("✅ Enhanced Llama Service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enhanced Llama Service: {e}")
            raise
    
    def _create_system_prompts(self) -> Dict[str, str]:
        """Create system prompts for different tasks"""
        return {
            'text_parsing': """You are a financial AI assistant specialized in parsing spending information from natural language text.

Your task is to extract structured spending data from user input and return it as valid JSON.

Extract these fields:
- amount: (required) The spending amount as a number
- currency: Currency code (default: "THB" for Thai Baht)
- merchant: Name of the store/merchant
- category: One of [Food & Dining, Transportation, Groceries, Shopping, Entertainment, Healthcare, Bills & Services, Travel, Education, Miscellaneous]
- subcategory: More specific category if applicable
- payment_method: One of [Cash, Credit Card, Debit Card, Bank Transfer, PromptPay, Mobile Banking, Digital Wallet, Other]
- date: ISO format date (use today's date if not specified)
- description: Brief description of the transaction
- location: Location if mentioned
- confidence: Your confidence score (0.0-1.0) in the extraction

IMPORTANT RULES:
1. Always return valid JSON format
2. If amount is missing or unclear, set confidence to 0.1
3. Use "Miscellaneous" for unclear categories
4. For Thai text, recognize common terms: บาท (baht), ซื้อ (buy), อาหาร (food), etc.
5. Be conservative with confidence scores
6. Handle various formats: "250 baht at McDonald's", "Lunch 120฿ cash", "Grabbed coffee ฿85"

Examples:
Input: "Lunch at McDonald's 250 baht cash"
Output: {"amount": 250, "currency": "THB", "merchant": "McDonald's", "category": "Food & Dining", "subcategory": "Fast Food", "payment_method": "Cash", "date": "2024-12-29T12:00:00", "description": "Lunch at McDonald's", "location": null, "confidence": 0.9}

Always respond with only the JSON object, no additional text.""",

            'enhancement': """You are a financial data enhancement expert. Your task is to improve and correct spending information extracted by local NLP systems.

You will receive:
1. Original text
2. Current NLP extraction results with confidence scores
3. Language information

Your job is to:
1. Correct any extraction errors
2. Fill in missing information
3. Improve categorization
4. Normalize merchant names
5. Provide reasoning for changes

Always return valid JSON with improved data and reasoning.""",

            'analysis': """You are a financial advisor and spending pattern analyst. Analyze spending data and provide actionable insights.

You will receive:
1. Summary of spending transactions
2. Category breakdowns
3. Time periods and trends

Provide:
1. Key insights about spending patterns
2. Actionable recommendations
3. Detected patterns and anomalies
4. Savings opportunities

Focus on practical, culturally appropriate advice for Thai users."""
        }
    
    async def _check_ollama_connection(self) -> bool:
        """Check if Ollama service is running"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ollama connection check failed: {str(e)}")
            return False
    
    async def _call_llama(self, prompt: str, system_prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Make API call to local Llama via Ollama"""
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.request_timeout)
                ) as session:
                    payload = {
                        "model": self.model,
                        "prompt": f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:",
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "num_predict": max_tokens,
                            "stop": ["User:", "Human:", "\n\n"]
                        }
                    }
                    
                    async with session.post(
                        f"{self.ollama_url}/api/generate",
                        json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get('response', '').strip()
                        else:
                            logger.error(f"Llama API error: {response.status}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Llama request timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise Exception("Llama request timeout after all retries")
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                logger.error(f"Llama API error on attempt {attempt + 1}: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Llama API failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def parse_spending_text(self, text: str, language: str = "en", context: Dict[str, Any] = None) -> NLPResult:
        """Parse spending text using Llama model"""
        try:
            logger.info(f"🦙 Parsing spending text with Llama: {text[:100]}...")
            
            if not await self._check_ollama_connection():
                raise Exception("Ollama service not available")
            
            # Prepare the prompt
            context_info = ""
            if context:
                context_info = f"\nContext: {json.dumps(context)}"
            
            user_prompt = f"""Parse this spending text and extract structured information:

Text: "{text}"
Language: {language}{context_info}

Return only valid JSON with the extracted spending information."""

            # Call Llama API
            response = await self._call_llama(
                user_prompt, 
                self.system_prompts['text_parsing'],
                max_tokens=600
            )
            
            if not response:
                raise Exception("No response from Llama model")
            
            # Parse the JSON response
            try:
                parsed_data = self._parse_llama_response(response)
                nlp_result = self._create_nlp_result(parsed_data, text)
                
                logger.info(f"✅ Llama parsing completed with {nlp_result.confidence:.2f} confidence")
                return nlp_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Llama response as JSON: {e}")
                logger.debug(f"Raw response: {response}")
                raise Exception("Failed to parse Llama response")
                
        except Exception as e:
            logger.error(f"❌ Llama parsing failed: {e}")
            raise Exception(f"Llama parsing failed: {str(e)}")
    
    async def enhance_nlp_result(self, text: str, nlp_result: NLPResult, language: str = "en") -> NLPResult:
        """Enhance NLP result using local Llama4"""
        try:
            logger.info("🦙 Enhancing NLP result with Llama4...")
            
            if not await self._check_ollama_connection():
                logger.warning("Ollama service not available for enhancement")
                return nlp_result
            
            user_prompt = f"""Enhance and correct this spending information extraction:

Original Text: "{text}"
Language: {language}

Current NLP Results (confidence: {nlp_result.confidence:.2f}):
- Merchant: {nlp_result.merchant or 'Not found'}
- Amount: {nlp_result.amount or 'Not found'}
- Category: {nlp_result.category or 'Not found'}
- Subcategory: {nlp_result.subcategory or 'Not found'}
- Payment Method: {nlp_result.payment_method or 'Not found'}
- Date: {nlp_result.date or 'Not found'}

Please provide enhanced extraction with corrections and improvements.
Return JSON format with reasoning for any changes made."""

            response = await self._call_llama(
                user_prompt,
                self.system_prompts['enhancement'],
                max_tokens=800
            )
            
            if response:
                enhanced_data = self._parse_llama_response(response)
                enhanced_result = self._merge_nlp_results(nlp_result, enhanced_data)
                
                logger.info(f"✅ Llama enhancement completed, confidence: {enhanced_result.confidence:.2f}")
                return enhanced_result
            else:
                logger.warning("No response from Llama for enhancement")
                return nlp_result
                
        except Exception as e:
            logger.error(f"❌ Llama enhancement failed: {e}")
            return nlp_result
    
    async def create_spending_entry(self, ocr_result: OCRResult, nlp_result: NLPResult, language: str = "en") -> NLPResult:
        """Create comprehensive spending entry using OCR + NLP + Llama4"""
        try:
            logger.info("🧠 Creating spending entry with Llama4 analysis...")
            
            if not await self._check_ollama_connection():
                logger.warning("Ollama service not available, returning NLP result")
                return nlp_result
            
            user_prompt = f"""Analyze this receipt data and create the most accurate spending entry:

OCR Text (confidence: {ocr_result.confidence:.2f}):
"{ocr_result.text}"

NLP Results (confidence: {nlp_result.confidence:.2f}):
- Merchant: {nlp_result.merchant}
- Amount: {nlp_result.amount}
- Category: {nlp_result.category}
- Payment Method: {nlp_result.payment_method}

Language: {language}

Combine both sources to extract:
1. Most accurate merchant name
2. Correct total amount (look for "total", "รวม", or final amount)
3. Best category classification
4. Payment method if visible
5. Transaction date if found
6. Clear description

Return JSON with your best analysis combining OCR and NLP data."""

            response = await self._call_llama(
                user_prompt,
                self.system_prompts['enhancement'],
                max_tokens=800
            )
            
            if response:
                llama_data = self._parse_llama_response(response)
                enhanced_result = self._create_comprehensive_result(ocr_result, nlp_result, llama_data)
                
                logger.info("✅ Llama spending entry created successfully")
                return enhanced_result
            else:
                logger.warning("No response from Llama, returning NLP result")
                return nlp_result
                
        except Exception as e:
            logger.error(f"❌ Llama spending entry creation failed: {e}")
            return nlp_result
    
    async def analyze_spending_patterns(self, entries: List[SpendingEntry], analysis_type: str = "comprehensive") -> AIAnalysis:
        """Llama4-powered spending pattern analysis"""
        try:
            logger.info(f"📊 Analyzing {len(entries)} spending entries with Llama4...")
            
            if not await self._check_ollama_connection():
                raise Exception("Ollama service not available")
            
            # Prepare data for analysis
            spending_summary = self._prepare_spending_summary(entries)
            
            user_prompt = f"""Analyze these spending patterns and provide comprehensive insights:

Spending Data Summary:
{json.dumps(spending_summary, indent=2)}

Analysis Type: {analysis_type}

Please provide detailed analysis including:
1. Key spending insights and trends
2. Actionable recommendations for better financial health
3. Detected patterns (weekly, monthly, seasonal)
4. Any unusual spending or anomalies
5. Specific savings opportunities

Consider Thai cultural context where applicable (festivals, family obligations, etc.).

Return structured JSON with insights, recommendations, patterns, and anomalies."""

            response = await self._call_llama(
                user_prompt,
                self.system_prompts['analysis'],
                max_tokens=1500
            )
            
            if response:
                analysis_data = self._parse_llama_response(response)
                analysis = self._create_ai_analysis(entries, analysis_data, analysis_type)
                
                logger.info("✅ Spending analysis completed with Llama4")
                return analysis
            else:
                raise Exception("No response from Llama for analysis")
                
        except Exception as e:
            logger.error(f"❌ Spending analysis failed: {e}")
            raise Exception(f"Llama4 analysis failed: {str(e)}")
    
    def _parse_llama_response(self, response: str) -> Dict[str, Any]:
        """Parse Llama response JSON with fallback"""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:]
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3]
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group()
            
            return json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Llama response as JSON: {str(e)}")
            logger.debug(f"Raw response: {response}")
            return {}
        except Exception as e:
            logger.error(f"Error processing Llama response: {str(e)}")
            return {}
    
    def _create_nlp_result(self, data: Dict[str, Any], original_text: str) -> NLPResult:
        """Create NLPResult from parsed Llama data"""
        try:
            # Parse date
            date_str = data.get("date")
            parsed_date = None
            if date_str:
                try:
                    parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    parsed_date = datetime.now()
            else:
                parsed_date = datetime.now()
            
            return NLPResult(
                merchant=data.get("merchant") or "Unknown Merchant",
                amount=float(data.get("amount", 0)),
                category=data.get("category") or "Miscellaneous",
                subcategory=data.get("subcategory"),
                date=parsed_date,
                payment_method=data.get("payment_method"),
                description=data.get("description") or f"Parsed: {original_text[:50]}",
                confidence=float(data.get("confidence", 0.8)),
                reasoning=data.get("reasoning", "Llama4 parsing"),
                extraction_details={
                    'llama_processed': True,
                    'model': self.model,
                    'original_text': original_text
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create NLPResult: {e}")
            return NLPResult(
                merchant="Llama Processing Error",
                amount=0,
                category="Miscellaneous",
                confidence=0.1,
                reasoning=f"Error: {str(e)}"
            )
    
    def _merge_nlp_results(self, original: NLPResult, enhanced_data: Dict[str, Any]) -> NLPResult:
        """Merge original NLP result with Llama enhancements"""
        try:
            # Parse enhanced date if provided
            enhanced_date = original.date
            if enhanced_data.get("date"):
                try:
                    enhanced_date = datetime.fromisoformat(enhanced_data["date"].replace("Z", "+00:00"))
                except:
                    pass  # Keep original date
            
            return NLPResult(
                merchant=enhanced_data.get("merchant") or original.merchant,
                amount=enhanced_data.get("amount") or original.amount,
                category=enhanced_data.get("category") or original.category,
                subcategory=enhanced_data.get("subcategory") or original.subcategory,
                date=enhanced_date,
                payment_method=enhanced_data.get("payment_method") or original.payment_method,
                description=enhanced_data.get("description") or original.description,
                confidence=max(original.confidence + 0.2, 0.85),  # Boost confidence
                reasoning=enhanced_data.get("reasoning", "Llama4 enhanced"),
                extraction_details={
                    **original.extraction_details,
                    'llama_enhanced': True,
                    'enhancement_model': self.model
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to merge NLP results: {e}")
            return original
    
    def _create_comprehensive_result(self, ocr_result: OCRResult, nlp_result: NLPResult, llama_data: Dict[str, Any]) -> NLPResult:
        """Create comprehensive result from OCR + NLP + Llama"""
        try:
            # Parse date from Llama data
            result_date = nlp_result.date
            if llama_data.get("date"):
                try:
                    result_date = datetime.fromisoformat(llama_data["date"].replace("Z", "+00:00"))
                except:
                    pass
            
            return NLPResult(
                merchant=llama_data.get("merchant") or nlp_result.merchant or "Receipt Entry",
                amount=llama_data.get("amount") or nlp_result.amount or 0.0,
                category=llama_data.get("category") or nlp_result.category or "Miscellaneous",
                subcategory=llama_data.get("subcategory") or nlp_result.subcategory,
                date=result_date,
                payment_method=llama_data.get("payment_method") or nlp_result.payment_method,
                description=llama_data.get("description") or f"Receipt from {llama_data.get('merchant', 'Unknown')}",
                confidence=0.9,  # High confidence for comprehensive processing
                reasoning=llama_data.get("reasoning", "Comprehensive OCR+NLP+Llama analysis"),
                extraction_details={
                    'comprehensive_processing': True,
                    'ocr_confidence': ocr_result.confidence,
                    'nlp_confidence': nlp_result.confidence,
                    'llama_model': self.model,
                    'processing_method': 'ocr+nlp+llama'
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create comprehensive result: {e}")
            return nlp_result
    
    def _prepare_spending_summary(self, entries: List[SpendingEntry]) -> Dict[str, Any]:
        """Prepare spending data summary for analysis"""
        if not entries:
            return {
                'total_entries': 0,
                'total_amount': 0,
                'message': 'No entries to analyze'
            }
        
        total_amount = sum(entry.amount for entry in entries)
        
        # Group by category
        categories = {}
        for entry in entries:
            cat = entry.category
            if cat not in categories:
                categories[cat] = {'count': 0, 'total': 0.0}
            categories[cat]['count'] += 1
            categories[cat]['total'] += entry.amount
        
        # Calculate averages
        for cat in categories:
            categories[cat]['avg'] = categories[cat]['total'] / categories[cat]['count']
        
        # Group by merchant (top 10)
        merchants = {}
        for entry in entries:
            merchant = entry.merchant
            if merchant not in merchants:
                merchants[merchant] = {'count': 0, 'total': 0.0}
            merchants[merchant]['count'] += 1
            merchants[merchant]['total'] += entry.amount
        
        top_merchants = dict(sorted(merchants.items(), key=lambda x: x[1]['total'], reverse=True)[:10])
        
        # Date range
        dates = [entry.date for entry in entries if entry.date]
        date_range = {}
        if dates:
            date_range = {
                'start': min(dates).isoformat()[:10],
                'end': max(dates).isoformat()[:10]
            }
        
        return {
            'total_entries': len(entries),
            'total_amount': total_amount,
            'average_transaction': total_amount / len(entries),
            'categories': categories,
            'top_merchants': top_merchants,
            'date_range': date_range
        }
    
    def _create_ai_analysis(self, entries: List[SpendingEntry], analysis_data: Dict[str, Any], analysis_type: str) -> AIAnalysis:
        """Create AIAnalysis from Llama response"""
        try:
            # Parse insights
            insights = []
            for insight_data in analysis_data.get('insights', []):
                if isinstance(insight_data, dict):
                    insights.append(AIInsight(
                        title=insight_data.get('title', 'Insight'),
                        description=insight_data.get('description', ''),
                        impact=insight_data.get('impact', 'medium')
                    ))
            
            # Parse recommendations
            recommendations = []
            for rec_data in analysis_data.get('recommendations', []):
                if isinstance(rec_data, dict):
                    recommendations.append(AIRecommendation(
                        action=rec_data.get('action', 'No action'),
                        reason=rec_data.get('reason', ''),
                        potential_savings=float(rec_data.get('potential_savings', 0.0))
                    ))
            
            # Parse anomalies
            anomalies = []
            for anomaly_data in analysis_data.get('anomalies', []):
                if isinstance(anomaly_data, dict):
                    anomalies.append(AIAnomaly(
                        description=anomaly_data.get('description', 'Anomaly detected'),
                        amount=float(anomaly_data.get('amount', 0.0)),
                        date=anomaly_data.get('date', datetime.now().isoformat()[:10])
                    ))
            
            return AIAnalysis(
                total_entries=len(entries),
                analysis_type=analysis_type,
                insights=insights,
                recommendations=recommendations,
                patterns=analysis_data.get('patterns', {}),
                anomalies=anomalies,
                confidence=0.85,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to create AI analysis: {e}")
            # Return basic analysis with error info
            return AIAnalysis(
                total_entries=len(entries),
                analysis_type=analysis_type,
                insights=[AIInsight(
                    title="Analysis Error",
                    description=f"Failed to process analysis: {str(e)}",
                    impact="low"
                )],
                recommendations=[],
                patterns={},
                anomalies=[],
                confidence=0.1,
                created_at=datetime.utcnow()
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Llama service is available"""
        try:
            if not await self._check_ollama_connection():
                return {
                    "status": "unhealthy",
                    "error": "Ollama service not available",
                    "model": self.model,
                    "url": self.ollama_url
                }
            
            # Try to get model information
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model.get("name") for model in data.get("models", [])]
                        return {
                            "status": "healthy",
                            "available_models": models,
                            "current_model": self.model,
                            "model_available": self.model in models,
                            "url": self.ollama_url
                        }
                    else:
                        return {
                            "status": "unhealthy", 
                            "error": f"HTTP {response.status}",
                            "model": self.model,
                            "url": self.ollama_url
                        }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "model": self.model,
                "url": self.ollama_url
            }
    
    async def ensure_model_available(self) -> bool:
        """Ensure the required model is available"""
        try:
            health = await self.health_check()
            if health.get("model_available"):
                return True
            
            logger.info(f"🦙 Model {self.model} not found, attempting to pull...")
            
            # Try to pull the model
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                payload = {"name": self.model}
                async with session.post(
                    f"{self.ollama_url}/api/pull",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Model {self.model} pulled successfully")
                        return True
                    else:
                        logger.error(f"❌ Failed to pull model: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Failed to ensure model availability: {e}")
            return False
