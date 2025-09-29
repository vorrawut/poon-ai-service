"""Spending category and payment method value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SpendingCategory(str, Enum):
    """Spending categories following Thai cultural context."""

    # Core categories
    FOOD_DINING = "Food & Dining"
    TRANSPORTATION = "Transportation"
    GROCERIES = "Groceries"
    SHOPPING = "Shopping"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    BILLS_UTILITIES = "Bills & Utilities"
    TRAVEL = "Travel"
    EDUCATION = "Education"

    # Thai cultural categories
    FAMILY_OBLIGATIONS = "Family Obligations"  # ภาระครอบครัว
    MERIT_MAKING = "Merit Making"  # การทำบุญ
    FESTIVAL_EXPENSES = "Festival Expenses"  # ค่าใช้จ่ายเทศกาล
    TEMPLE_DONATIONS = "Temple Donations"  # บริจาควัด

    # Other
    MISCELLANEOUS = "Miscellaneous"

    @classmethod
    def from_thai_text(cls, thai_text: str) -> SpendingCategory:
        """Map Thai text to spending category."""
        thai_mapping = {
            "อาหาร": cls.FOOD_DINING,
            "กิน": cls.FOOD_DINING,
            "ร้านอาหาร": cls.FOOD_DINING,
            "กาแฟ": cls.FOOD_DINING,
            "ข้าว": cls.FOOD_DINING,
            "รถ": cls.TRANSPORTATION,
            "แท็กซี่": cls.TRANSPORTATION,
            "น้ำมัน": cls.TRANSPORTATION,
            "ซื้อของ": cls.GROCERIES,
            "ตลาด": cls.GROCERIES,
            "ห้าง": cls.SHOPPING,
            "เสื้อผ้า": cls.SHOPPING,
            "หนัง": cls.ENTERTAINMENT,
            "เกม": cls.ENTERTAINMENT,
            "หมอ": cls.HEALTHCARE,
            "โรงพยาบาล": cls.HEALTHCARE,
            "ยา": cls.HEALTHCARE,
            "ทำบุญ": cls.MERIT_MAKING,
            "วัด": cls.TEMPLE_DONATIONS,
            "เทศกาล": cls.FESTIVAL_EXPENSES,
            "ครอบครัว": cls.FAMILY_OBLIGATIONS,
        }

        text_lower = thai_text.lower()
        for thai_term, category in thai_mapping.items():
            if thai_term in text_lower:
                return category

        return cls.MISCELLANEOUS

    def get_thai_name(self) -> str:
        """Get Thai name for the category."""
        thai_names = {
            self.FOOD_DINING: "อาหารและเครื่องดื่ม",
            self.TRANSPORTATION: "การเดินทาง",
            self.GROCERIES: "ของใช้ประจำวัน",
            self.SHOPPING: "ช้อปปิ้ง",
            self.ENTERTAINMENT: "บันเทิง",
            self.HEALTHCARE: "สุขภาพ",
            self.BILLS_UTILITIES: "ค่าบิลและสาธารณูปโภค",
            self.TRAVEL: "ท่องเที่ยว",
            self.EDUCATION: "การศึกษา",
            self.FAMILY_OBLIGATIONS: "ภาระครอบครัว",
            self.MERIT_MAKING: "การทำบุญ",
            self.FESTIVAL_EXPENSES: "ค่าใช้จ่ายเทศกาล",
            self.TEMPLE_DONATIONS: "บริจาควัด",
            self.MISCELLANEOUS: "อื่นๆ",
        }
        return thai_names.get(self, self.value)

    def is_cultural(self) -> bool:
        """Check if this is a Thai cultural category."""
        cultural_categories = {
            self.FAMILY_OBLIGATIONS,
            self.MERIT_MAKING,
            self.FESTIVAL_EXPENSES,
            self.TEMPLE_DONATIONS,
        }
        return self in cultural_categories

    def is_essential(self) -> bool:
        """Check if this is an essential spending category."""
        essential_categories = {
            self.FOOD_DINING,
            self.GROCERIES,
            self.HEALTHCARE,
            self.BILLS_UTILITIES,
            self.TRANSPORTATION,
        }
        return self in essential_categories


class PaymentMethod(str, Enum):
    """Payment methods common in Thailand."""

    CASH = "Cash"  # เงินสด
    CREDIT_CARD = "Credit Card"  # บัตรเครดิต
    DEBIT_CARD = "Debit Card"  # บัตรเดบิต
    BANK_TRANSFER = "Bank Transfer"  # โอนเงิน
    PROMPTPAY = "PromptPay"  # พร้อมเพย์
    MOBILE_BANKING = "Mobile Banking"  # แอปธนาคาร
    DIGITAL_WALLET = "Digital Wallet"  # กระเป๋าเงินดิจิทัล
    QR_CODE = "QR Code"  # คิวอาร์โค้ด
    OTHER = "Other"

    @classmethod
    def from_thai_text(cls, thai_text: str) -> PaymentMethod:
        """Map Thai text to payment method."""
        thai_mapping = {
            "เงินสด": cls.CASH,
            "สด": cls.CASH,
            "บัตรเครดิต": cls.CREDIT_CARD,
            "เครดิต": cls.CREDIT_CARD,
            "บัตรเดบิต": cls.DEBIT_CARD,
            "เดบิต": cls.DEBIT_CARD,
            "บัตร": cls.CREDIT_CARD,  # Default to credit card
            "โอน": cls.BANK_TRANSFER,
            "โอนเงิน": cls.BANK_TRANSFER,
            "พร้อมเพย์": cls.PROMPTPAY,
            "promptpay": cls.PROMPTPAY,
            "แอป": cls.MOBILE_BANKING,
            "มือถือ": cls.MOBILE_BANKING,
            "คิวอาร์": cls.QR_CODE,
            "qr": cls.QR_CODE,
        }

        text_lower = thai_text.lower()
        for thai_term, method in thai_mapping.items():
            if thai_term in text_lower:
                return method

        return cls.OTHER

    def get_thai_name(self) -> str:
        """Get Thai name for the payment method."""
        thai_names = {
            self.CASH: "เงินสด",
            self.CREDIT_CARD: "บัตรเครดิต",
            self.DEBIT_CARD: "บัตรเดบิต",
            self.BANK_TRANSFER: "โอนเงิน",
            self.PROMPTPAY: "พร้อมเพย์",
            self.MOBILE_BANKING: "แอปธนาคาร",
            self.DIGITAL_WALLET: "กระเป๋าเงินดิจิทัล",
            self.QR_CODE: "คิวอาร์โค้ด",
            self.OTHER: "อื่นๆ",
        }
        return thai_names.get(self, self.value)

    def is_digital(self) -> bool:
        """Check if this is a digital payment method."""
        digital_methods = {
            self.CREDIT_CARD,
            self.DEBIT_CARD,
            self.BANK_TRANSFER,
            self.PROMPTPAY,
            self.MOBILE_BANKING,
            self.DIGITAL_WALLET,
            self.QR_CODE,
        }
        return self in digital_methods

    def is_instant(self) -> bool:
        """Check if this payment method is instant."""
        instant_methods = {
            self.CASH,
            self.PROMPTPAY,
            self.QR_CODE,
            self.DIGITAL_WALLET,
        }
        return self in instant_methods


@dataclass(frozen=True)
class CategoryConfidence:
    """Category classification with confidence score."""

    category: SpendingCategory
    confidence: float
    reasoning: str | None = None

    def __post_init__(self) -> None:
        """Validate category confidence."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            raise ValueError(msg)

    def is_reliable(self) -> bool:
        """Check if classification is reliable (>= 0.7)."""
        return self.confidence >= 0.7

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, CategoryConfidence):
            return False
        return (
            self.category == other.category
            and abs(self.confidence - other.confidence) < 1e-6
        )
