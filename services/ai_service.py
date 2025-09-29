"""
AI Service for enhanced spending analysis using OpenAI GPT
Only used as fallback when local processing confidence is low
Cost-optimized approach
"""

import openai
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.spending_models import NLPResult, OCRResult, SpendingEntry, AIAnalysis, AIInsight, AIRecommendation, AIAnomaly
import time

logger = logging.getLogger(__name__)

class AIService:
    """AI service using OpenAI for enhanced processing"""
    
    def __init__(self, settings):
        self.settings = settings
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Cost-efficient model
        self.max_retries = 3
        self.request_timeout = 30
    
    async def enhance_nlp_result(self, text: str, nlp_result: NLPResult, language: str = "en") -> NLPResult:
        """
        Enhance NLP result using AI when local confidence is low
        """
        try:
            logger.info("🤖 Enhancing NLP result with AI...")
            
            prompt = self._create_nlp_enhancement_prompt(text, nlp_result, language)
            
            response = await self._call_openai(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent results
            )
            
            enhanced_data = self._parse_ai_response(response)
            
            # Merge with existing result, AI takes precedence for missing fields
            enhanced_result = NLPResult(
                merchant=enhanced_data.get('merchant') or nlp_result.merchant,
                amount=enhanced_data.get('amount') or nlp_result.amount,
                category=enhanced_data.get('category') or nlp_result.category,
                subcategory=enhanced_data.get('subcategory') or nlp_result.subcategory,
                date=enhanced_data.get('date') or nlp_result.date,
                payment_method=enhanced_data.get('payment_method') or nlp_result.payment_method,
                description=enhanced_data.get('description') or nlp_result.description,
                confidence=max(0.85, nlp_result.confidence + 0.2),  # AI boost
                reasoning=enhanced_data.get('reasoning', 'AI enhanced'),
                extraction_details={
                    **nlp_result.extraction_details,
                    'ai_enhanced': True,
                    'ai_model': self.model
                }
            )
            
            logger.info(f"✅ AI enhancement completed, confidence boosted to {enhanced_result.confidence:.2f}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ AI enhancement failed: {str(e)}")
            # Return original result if AI fails
            return nlp_result
    
    async def create_spending_entry(self, ocr_result: OCRResult, nlp_result: NLPResult, language: str = "en") -> NLPResult:
        """
        Create comprehensive spending entry using OCR + NLP + AI
        """
        try:
            logger.info("🧠 Creating spending entry with AI analysis...")
            
            prompt = self._create_comprehensive_prompt(ocr_result, nlp_result, language)
            
            response = await self._call_openai(
                prompt=prompt,
                max_tokens=800,
                temperature=0.1
            )
            
            ai_data = self._parse_ai_response(response)
            
            # Create enhanced result
            enhanced_result = NLPResult(
                merchant=ai_data.get('merchant', 'AI Processed Entry'),
                amount=ai_data.get('amount', 0.0),
                category=ai_data.get('category', 'Miscellaneous'),
                subcategory=ai_data.get('subcategory'),
                date=ai_data.get('date', datetime.utcnow()),
                payment_method=ai_data.get('payment_method'),
                description=ai_data.get('description', 'AI processed receipt'),
                confidence=0.9,  # High confidence for AI processing
                reasoning=ai_data.get('reasoning', 'Comprehensive AI analysis'),
                extraction_details={
                    'ai_processed': True,
                    'ocr_confidence': ocr_result.confidence,
                    'nlp_confidence': nlp_result.confidence,
                    'ai_model': self.model
                }
            )
            
            logger.info("✅ AI spending entry created successfully")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ AI spending entry creation failed: {str(e)}")
            # Fallback to NLP result
            return nlp_result
    
    async def enhance_text_parsing(self, text: str, nlp_result: NLPResult, language: str = "en", context: Dict[str, Any] = None) -> NLPResult:
        """
        Enhanced text parsing for voice/chat input
        """
        try:
            logger.info("💬 Enhancing text parsing with AI...")
            
            prompt = self._create_text_parsing_prompt(text, nlp_result, language, context)
            
            response = await self._call_openai(
                prompt=prompt,
                max_tokens=600,
                temperature=0.2
            )
            
            ai_data = self._parse_ai_response(response)
            
            enhanced_result = NLPResult(
                merchant=ai_data.get('merchant') or nlp_result.merchant or 'Voice/Chat Entry',
                amount=ai_data.get('amount') or nlp_result.amount or 0.0,
                category=ai_data.get('category') or nlp_result.category or 'Miscellaneous',
                subcategory=ai_data.get('subcategory') or nlp_result.subcategory,
                date=ai_data.get('date') or nlp_result.date or datetime.utcnow(),
                payment_method=ai_data.get('payment_method') or nlp_result.payment_method,
                description=ai_data.get('description') or text[:100],
                confidence=0.88,
                reasoning=ai_data.get('reasoning', 'AI enhanced text parsing'),
                extraction_details={
                    **nlp_result.extraction_details,
                    'ai_text_enhanced': True,
                    'original_text': text
                }
            )
            
            logger.info("✅ Text parsing enhancement completed")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Text parsing enhancement failed: {str(e)}")
            return nlp_result
    
    async def analyze_spending_patterns(self, entries: List[SpendingEntry], analysis_type: str = "comprehensive") -> AIAnalysis:
        """
        AI-powered spending pattern analysis
        """
        try:
            logger.info(f"📊 Analyzing {len(entries)} spending entries with AI...")
            
            # Prepare data for analysis
            spending_summary = self._prepare_spending_summary(entries)
            
            prompt = self._create_analysis_prompt(spending_summary, analysis_type)
            
            response = await self._call_openai(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3
            )
            
            analysis_data = self._parse_analysis_response(response)
            
            analysis = AIAnalysis(
                total_entries=len(entries),
                analysis_type=analysis_type,
                insights=analysis_data.get('insights', []),
                recommendations=analysis_data.get('recommendations', []),
                patterns=analysis_data.get('patterns', {}),
                anomalies=analysis_data.get('anomalies', []),
                confidence=0.85,
                created_at=datetime.utcnow()
            )
            
            logger.info("✅ Spending analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Spending analysis failed: {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")
    
    async def enhance_spending_entry(self, entry: SpendingEntry) -> SpendingEntry:
        """
        Enhance individual spending entry with AI insights
        """
        try:
            prompt = f"""
            Enhance this spending entry with better categorization and insights:
            
            Current Entry:
            - Merchant: {entry.merchant}
            - Amount: ฿{entry.amount}
            - Category: {entry.category}
            - Description: {entry.description}
            - Date: {entry.date}
            
            Please provide:
            1. Better category if current is wrong
            2. Appropriate subcategory
            3. Improved description
            4. Any insights about this spending
            
            Return JSON format:
            {{"category": "...", "subcategory": "...", "description": "...", "insights": "..."}}
            """
            
            response = await self._call_openai(prompt=prompt, max_tokens=400, temperature=0.2)
            ai_data = self._parse_ai_response(response)
            
            # Update entry with AI enhancements
            enhanced_entry = SpendingEntry(
                **entry.dict(),
                category=ai_data.get('category', entry.category),
                subcategory=ai_data.get('subcategory', entry.subcategory),
                description=ai_data.get('description', entry.description),
                confidence=min(entry.confidence + 0.15, 1.0),
                metadata={
                    **entry.metadata,
                    'ai_enhanced': True,
                    'ai_insights': ai_data.get('insights', '')
                }
            )
            
            return enhanced_entry
            
        except Exception as e:
            logger.error(f"❌ Entry enhancement failed: {str(e)}")
            return entry
    
    def _create_nlp_enhancement_prompt(self, text: str, nlp_result: NLPResult, language: str) -> str:
        """Create prompt for NLP enhancement"""
        return f"""
        Analyze this spending text and extract structured information. The local NLP system had low confidence.
        
        Text: "{text}"
        Language: {language}
        
        Current extraction (low confidence):
        - Merchant: {nlp_result.merchant or 'Not found'}
        - Amount: {nlp_result.amount or 'Not found'}
        - Category: {nlp_result.category or 'Not found'}
        - Payment Method: {nlp_result.payment_method or 'Not found'}
        
        Please extract and correct:
        1. Merchant/Store name (clean and normalize)
        2. Amount in numbers (remove currency symbols)
        3. Most appropriate category from: Food & Dining, Transportation, Groceries, Shopping, Entertainment, Healthcare, Bills & Services, Travel, Education, Miscellaneous
        4. Subcategory if applicable
        5. Payment method: Cash, Credit Card, Debit Card, Bank Transfer, PromptPay, Mobile Banking, Digital Wallet, Other
        6. Brief reasoning for your decisions
        
        Return JSON format only:
        {{"merchant": "...", "amount": 0.00, "category": "...", "subcategory": "...", "payment_method": "...", "description": "...", "reasoning": "..."}}
        """
    
    def _create_comprehensive_prompt(self, ocr_result: OCRResult, nlp_result: NLPResult, language: str) -> str:
        """Create comprehensive analysis prompt"""
        return f"""
        Analyze this receipt using OCR text and NLP results to create a complete spending entry.
        
        OCR Text (confidence: {ocr_result.confidence:.2f}):
        "{ocr_result.text}"
        
        NLP Results (confidence: {nlp_result.confidence:.2f}):
        - Merchant: {nlp_result.merchant}
        - Amount: {nlp_result.amount}
        - Category: {nlp_result.category}
        - Payment Method: {nlp_result.payment_method}
        
        Please provide the most accurate extraction by combining both sources:
        1. Merchant name (clean and standardized)
        2. Total amount (look for "total", "รวม", or final amount)
        3. Best category from: Food & Dining, Transportation, Groceries, Shopping, Entertainment, Healthcare, Bills & Services, Travel, Education, Miscellaneous
        4. Subcategory if clear from context
        5. Payment method if mentioned
        6. Transaction date if found
        7. Brief description
        8. Your reasoning process
        
        Return JSON format:
        {{"merchant": "...", "amount": 0.00, "category": "...", "subcategory": "...", "payment_method": "...", "date": "YYYY-MM-DD", "description": "...", "reasoning": "..."}}
        """
    
    def _create_text_parsing_prompt(self, text: str, nlp_result: NLPResult, language: str, context: Dict[str, Any] = None) -> str:
        """Create text parsing prompt for voice/chat"""
        context_info = ""
        if context:
            context_info = f"\nAdditional context: {json.dumps(context)}"
        
        return f"""
        Parse this natural language spending description into structured data:
        
        Text: "{text}"
        Language: {language}{context_info}
        
        Current NLP extraction:
        - Merchant: {nlp_result.merchant}
        - Amount: {nlp_result.amount}
        - Category: {nlp_result.category}
        
        Please extract:
        1. Merchant/business name
        2. Amount spent (numbers only)
        3. Most suitable category
        4. Payment method if mentioned
        5. When it happened (relative to today)
        6. Clean description
        
        Examples of good parsing:
        "Coffee at Starbucks 120 baht by card" → Merchant: Starbucks, Amount: 120, Category: Food & Dining, Payment: Credit Card
        "ซื้อข้าว 50 บาท เงินสด" → Merchant: Restaurant, Amount: 50, Category: Food & Dining, Payment: Cash
        
        Return JSON:
        {{"merchant": "...", "amount": 0.00, "category": "...", "payment_method": "...", "date": "YYYY-MM-DD", "description": "...", "reasoning": "..."}}
        """
    
    def _create_analysis_prompt(self, spending_summary: Dict[str, Any], analysis_type: str) -> str:
        """Create spending analysis prompt"""
        return f"""
        Analyze these spending patterns and provide insights:
        
        Spending Summary:
        {json.dumps(spending_summary, indent=2)}
        
        Analysis Type: {analysis_type}
        
        Please provide:
        1. Key insights about spending patterns
        2. Actionable recommendations for better financial health
        3. Detected patterns (weekly, monthly, category-based)
        4. Any anomalies or unusual spending
        5. Opportunities for savings
        
        Focus on practical, actionable advice that helps users improve their financial habits.
        
        Return JSON format:
        {{
            "insights": [
                {{"title": "...", "description": "...", "impact": "high/medium/low"}},
                ...
            ],
            "recommendations": [
                {{"action": "...", "reason": "...", "potential_savings": 0.00}},
                ...
            ],
            "patterns": {{
                "weekly": "...",
                "monthly": "...",
                "categories": "..."
            }},
            "anomalies": [
                {{"description": "...", "amount": 0.00, "date": "..."}},
                ...
            ]
        }}
        """
    
    def _prepare_spending_summary(self, entries: List[SpendingEntry]) -> Dict[str, Any]:
        """Prepare spending data summary for analysis"""
        total_amount = sum(entry.amount for entry in entries)
        
        # Group by category
        categories = {}
        for entry in entries:
            cat = entry.category
            if cat not in categories:
                categories[cat] = {'count': 0, 'total': 0.0, 'avg': 0.0}
            categories[cat]['count'] += 1
            categories[cat]['total'] += entry.amount
        
        for cat in categories:
            categories[cat]['avg'] = categories[cat]['total'] / categories[cat]['count']
        
        # Group by merchant
        merchants = {}
        for entry in entries:
            merchant = entry.merchant
            if merchant not in merchants:
                merchants[merchant] = {'count': 0, 'total': 0.0}
            merchants[merchant]['count'] += 1
            merchants[merchant]['total'] += entry.amount
        
        return {
            'total_entries': len(entries),
            'total_amount': total_amount,
            'average_transaction': total_amount / len(entries) if entries else 0,
            'categories': categories,
            'top_merchants': dict(sorted(merchants.items(), key=lambda x: x[1]['total'], reverse=True)[:10]),
            'date_range': {
                'start': min(entry.date for entry in entries).isoformat() if entries else None,
                'end': max(entry.date for entry in entries).isoformat() if entries else None
            }
        }
    
    async def _call_openai(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> str:
        """Make API call to OpenAI with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a financial data extraction expert. Always return valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=self.request_timeout
                    ),
                    timeout=self.request_timeout
                )
                
                return response.choices[0].message.content.strip()
                
            except asyncio.TimeoutError:
                logger.warning(f"OpenAI request timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise Exception("OpenAI request timeout after all retries")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"OpenAI API failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response JSON"""
        try:
            # Clean response (remove markdown code blocks if present)
            if response.startswith('```json'):
                response = response[7:-3]
            elif response.startswith('```'):
                response = response[3:-3]
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.debug(f"Raw response: {response}")
            return {}
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse analysis response with fallback"""
        try:
            return self._parse_ai_response(response)
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {str(e)}")
            return {
                'insights': [{'title': 'Analysis Error', 'description': 'Failed to parse AI response', 'impact': 'low'}],
                'recommendations': [],
                'patterns': {},
                'anomalies': []
            }
