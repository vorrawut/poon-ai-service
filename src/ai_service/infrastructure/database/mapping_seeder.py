"""Database seeder for initial category mappings."""

from __future__ import annotations

import structlog

from ...domain.entities.category_mapping import (
    CategoryMapping,
    MappingSource,
    MappingStatus,
    MappingType,
)
from ...domain.repositories.category_mapping_repository import CategoryMappingRepository

logger = structlog.get_logger(__name__)


class MappingSeeder:
    """Seeder for initial category mappings."""

    def __init__(self, repository: CategoryMappingRepository) -> None:
        self._repository = repository

    async def seed_initial_mappings(self) -> int:
        """Seed database with initial comprehensive mappings."""
        try:
            mappings = self._get_initial_mappings()

            # Check if mappings already exist
            existing_mappings = await self._repository.get_all_active_mappings()
            if existing_mappings:
                logger.info(
                    f"Found {len(existing_mappings)} existing mappings, skipping seed"
                )
                return 0

            # Bulk create mappings
            created_count = await self._repository.bulk_create_mappings(mappings)

            logger.info(f"Seeded {created_count} initial category mappings")
            return created_count

        except Exception as e:
            logger.error(f"Failed to seed initial mappings: {e}")
            raise

    def _get_initial_mappings(self) -> list[CategoryMapping]:
        """Get list of initial mappings to seed."""
        mappings = []

        # English mappings
        english_mappings = [
            # Food & Dining
            (
                "food",
                "Food & Dining",
                ["meal", "eat", "dining"],
                ["food.*", "eat.*", "meal.*"],
            ),
            (
                "restaurant",
                "Food & Dining",
                ["cafe", "diner", "eatery"],
                ["restaurant.*", "cafe.*"],
            ),
            (
                "coffee",
                "Food & Dining",
                ["starbucks", "cafe", "espresso"],
                ["coffee.*", "starbucks.*"],
            ),
            (
                "lunch",
                "Food & Dining",
                ["dinner", "breakfast"],
                ["lunch.*", "dinner.*", "breakfast.*"],
            ),
            ("pizza", "Food & Dining", ["dominos", "pizza hut"], ["pizza.*"]),
            (
                "burger",
                "Food & Dining",
                ["mcdonalds", "burger king", "kfc"],
                ["burger.*", "mcdonald.*", "kfc.*"],
            ),
            # Transportation
            (
                "taxi",
                "Transportation",
                ["uber", "grab", "lyft"],
                ["taxi.*", "uber.*", "grab.*"],
            ),
            (
                "bus",
                "Transportation",
                ["public transport", "transit"],
                ["bus.*", "transit.*"],
            ),
            (
                "train",
                "Transportation",
                ["railway", "subway", "metro"],
                ["train.*", "railway.*", "subway.*", "metro.*"],
            ),
            (
                "gas",
                "Transportation",
                ["fuel", "petrol", "gasoline"],
                ["gas.*", "fuel.*", "petrol.*"],
            ),
            ("parking", "Transportation", ["car park"], ["parking.*"]),
            # Shopping
            (
                "shopping",
                "Shopping",
                ["shop", "store", "mall"],
                ["shop.*", "store.*", "mall.*"],
            ),
            (
                "clothes",
                "Shopping",
                ["clothing", "fashion", "apparel"],
                ["cloth.*", "fashion.*", "apparel.*"],
            ),
            (
                "electronics",
                "Shopping",
                ["gadgets", "tech"],
                ["electronic.*", "gadget.*", "tech.*"],
            ),
            # Travel
            (
                "hotel",
                "Travel",
                ["accommodation", "lodging", "resort"],
                ["hotel.*", "resort.*", "lodging.*"],
            ),
            (
                "flight",
                "Travel",
                ["airline", "airplane"],
                ["flight.*", "airline.*", "airplane.*"],
            ),
            ("booking", "Travel", ["reservation"], ["booking.*", "reservation.*"]),
            # Groceries
            (
                "grocery",
                "Groceries",
                ["supermarket", "market"],
                ["grocery.*", "supermarket.*", "market.*"],
            ),
            (
                "walmart",
                "Groceries",
                ["target", "costco"],
                ["walmart.*", "target.*", "costco.*"],
            ),
            # Healthcare
            (
                "hospital",
                "Healthcare",
                ["medical", "clinic"],
                ["hospital.*", "medical.*", "clinic.*"],
            ),
            (
                "pharmacy",
                "Healthcare",
                ["medicine", "drug store"],
                ["pharmacy.*", "medicine.*", "drug.*"],
            ),
            (
                "doctor",
                "Healthcare",
                ["physician", "dentist"],
                ["doctor.*", "physician.*", "dentist.*"],
            ),
            # Entertainment
            (
                "movie",
                "Entertainment",
                ["cinema", "theater"],
                ["movie.*", "cinema.*", "theater.*"],
            ),
            ("game", "Entertainment", ["gaming", "video game"], ["game.*", "gaming.*"]),
            (
                "music",
                "Entertainment",
                ["concert", "spotify"],
                ["music.*", "concert.*", "spotify.*"],
            ),
            # Utilities
            (
                "electric",
                "Utilities",
                ["electricity", "power"],
                ["electric.*", "power.*"],
            ),
            ("water", "Utilities", ["utility"], ["water.*"]),
            (
                "internet",
                "Utilities",
                ["wifi", "broadband"],
                ["internet.*", "wifi.*", "broadband.*"],
            ),
            (
                "phone",
                "Utilities",
                ["mobile", "cell"],
                ["phone.*", "mobile.*", "cell.*"],
            ),
        ]

        for key, category, aliases, patterns in english_mappings:
            mapping = CategoryMapping(
                key=key,
                mapping_type=MappingType.CATEGORY,
                language="en",
                target_category=category,
                aliases=aliases,
                patterns=patterns,
                confidence=0.9,
                source=MappingSource.MANUAL,
                status=MappingStatus.ACTIVE,
                priority=10,
            )
            mappings.append(mapping)

        # Thai mappings
        thai_mappings = [
            # Food & Dining
            (
                "อาหาร",
                "Food & Dining",
                ["กิน", "ทาน", "เสวย"],
                ["อาหาร.*", "กิน.*", "ทาน.*"],
            ),
            (
                "ร้านอาหาร",
                "Food & Dining",
                ["ร้าน", "ภัตตาคาร"],
                ["ร้านอาหาร.*", "ภัตตาคาร.*"],
            ),
            (
                "กาแฟ",
                "Food & Dining",
                ["สตาร์บัคส์", "คาเฟ่"],
                ["กาแฟ.*", "สตาร์บัคส์.*", "คาเฟ่.*"],
            ),
            (
                "ข้าว",
                "Food & Dining",
                ["อาหารเที่ยง", "อาหารเย็น"],
                ["ข้าว.*", "อาหารเที่ยง.*", "อาหารเย็น.*"],
            ),
            # Transportation
            ("แท็กซี่", "Transportation", ["รถแท็กซี่", "วิน"], ["แท็กซี่.*", "วิน.*"]),
            (
                "รถเมล์",
                "Transportation",
                ["รถประจำทาง", "รถบัส"],
                ["รถเมล์.*", "รถประจำทาง.*", "รถบัส.*"],
            ),
            (
                "รถไฟ",
                "Transportation",
                ["รถไฟฟ้า", "BTS", "MRT"],
                ["รถไฟ.*", "BTS.*", "MRT.*"],
            ),
            ("น้ำมัน", "Transportation", ["เชื้อเฟื้อง"], ["น้ำมัน.*", "เชื้อเฟื้อง.*"]),
            # Shopping
            ("ซื้อของ", "Shopping", ["ช้อป", "ช้อปปิ้ง"], ["ซื้อของ.*", "ช้อป.*", "ช้อปปิ้ง.*"]),
            ("เสื้อผ้า", "Shopping", ["แฟชั่น"], ["เสื้อผ้า.*", "แฟชั่น.*"]),
            ("ห้าง", "Shopping", ["ห้างสรรพสินค้า", "เซ็นทรัล"], ["ห้าง.*", "เซ็นทรัล.*"]),
            # Travel
            ("โรงแรม", "Travel", ["ที่พัก", "รีสอร์ท"], ["โรงแรม.*", "ที่พัก.*", "รีสอร์ท.*"]),
            ("เที่ยวบิน", "Travel", ["สายการบิน"], ["เที่ยวบิน.*", "สายการบิน.*"]),
            ("จอง", "Travel", ["จองห้อง"], ["จอง.*"]),
            # Groceries
            ("ตลาด", "Groceries", ["ซุปเปอร์มาร์เก็ต"], ["ตลาด.*", "ซุปเปอร์.*"]),
            (
                "เซเว่น",
                "Groceries",
                ["7-11", "เทสโก้", "บิ๊กซี"],
                ["เซเว่น.*", "7-11.*", "เทสโก้.*", "บิ๊กซี.*"],
            ),
            # Healthcare
            (
                "โรงพยาบาล",
                "Healthcare",
                ["หมอ", "คลินิก"],
                ["โรงพยาบาล.*", "หมอ.*", "คลินิก.*"],
            ),
            ("ร้านยา", "Healthcare", ["ยา"], ["ร้านยา.*", "ยา.*"]),
            # Entertainment
            (
                "หนัง",
                "Entertainment",
                ["โรงหนัง", "ภาพยนตร์"],
                ["หนัง.*", "โรงหนัง.*", "ภาพยนตร์.*"],
            ),
            ("เกม", "Entertainment", ["เกมส์"], ["เกม.*"]),
            ("ดนตรี", "Entertainment", ["คอนเสิร์ต"], ["ดนตรี.*", "คอนเสิร์ต.*"]),
            # Utilities
            ("ไฟฟ้า", "Utilities", ["กระแสไฟฟ้า"], ["ไฟฟ้า.*"]),
            ("น้ำประปา", "Utilities", ["น้ำ"], ["น้ำประปา.*", "น้ำ.*"]),
            (
                "อินเทอร์เน็ต",
                "Utilities",
                ["เน็ต", "wifi"],
                ["อินเทอร์เน็ต.*", "เน็ต.*", "wifi.*"],
            ),
            ("โทรศัพท์", "Utilities", ["มือถือ"], ["โทรศัพท์.*", "มือถือ.*"]),
        ]

        for key, category, aliases, patterns in thai_mappings:
            mapping = CategoryMapping(
                key=key,
                mapping_type=MappingType.CATEGORY,
                language="th",
                target_category=category,
                aliases=aliases,
                patterns=patterns,
                confidence=0.9,
                source=MappingSource.MANUAL,
                status=MappingStatus.ACTIVE,
                priority=10,
            )
            mappings.append(mapping)

        return mappings

    async def seed_test_candidates(self) -> int:
        """Seed database with test mapping candidates."""
        try:
            from ...domain.entities.category_mapping import MappingCandidate

            candidates = [
                MappingCandidate(
                    original_text="bought some snacks at 7-eleven",
                    normalized_text="snacks 7-eleven",
                    language="en",
                    suggested_category="Groceries",
                    suggested_confidence=0.8,
                    suggestion_source="heuristic",
                ),
                MappingCandidate(
                    original_text="ซื้อขนมที่เซเว่น",
                    normalized_text="ขนม เซเว่น",
                    language="th",
                    suggested_category="Groceries",
                    suggested_confidence=0.8,
                    suggestion_source="heuristic",
                ),
                MappingCandidate(
                    original_text="netflix subscription",
                    normalized_text="netflix subscription",
                    language="en",
                    suggested_category="Entertainment",
                    suggested_confidence=0.7,
                    suggestion_source="heuristic",
                ),
            ]

            for candidate in candidates:
                await self._repository.save_candidate(candidate)

            logger.info(f"Seeded {len(candidates)} test candidates")
            return len(candidates)

        except Exception as e:
            logger.error(f"Failed to seed test candidates: {e}")
            return 0
